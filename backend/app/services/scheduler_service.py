from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from datetime import datetime
import logging
import re

from app.config import settings

logger = logging.getLogger(__name__)


class SchedulerService:
    def __init__(self):
        self.scheduler = BackgroundScheduler()

    def start(self):
        if not self.scheduler.running:
            self.scheduler.start()
            self._add_system_jobs()
            logger.info("Scheduler started")

    def shutdown(self):
        if self.scheduler.running:
            self.scheduler.shutdown()

    def _add_system_jobs(self):
        # Process queue every 30 minutes (daily limit controls actual output)
        self.scheduler.add_job(
            self._process_queue,
            "interval",
            minutes=30,
            id="process_queue",
            replace_existing=True,
        )
        # Check mentions every 2 minutes
        self.scheduler.add_job(
            self._check_mentions,
            "interval",
            minutes=2,
            id="check_mentions",
            replace_existing=True,
        )
        # Sync analytics every hour
        self.scheduler.add_job(
            self._sync_analytics,
            "interval",
            hours=1,
            id="sync_analytics",
            replace_existing=True,
        )
        # FlippX bot cycle
        self.scheduler.add_job(
            self._run_bot_cycle,
            "interval",
            minutes=settings.TWEET_INTERVAL_MINUTES,
            id="bot_cycle",
            replace_existing=True,
        )
        # Auto-refill queue when below 20 pending tweets
        self.scheduler.add_job(
            self._refill_queue,
            "interval",
            minutes=30,
            id="refill_queue",
            replace_existing=True,
        )

    def schedule_tweet(self, tweet_id: int, scheduled_at: datetime, content: str) -> str:
        job_id = f"tweet_{tweet_id}"
        self.scheduler.add_job(
            self._send_scheduled_tweet,
            DateTrigger(run_date=scheduled_at),
            args=[tweet_id],
            id=job_id,
            replace_existing=True,
        )
        logger.info(f"Scheduled tweet {tweet_id} at {scheduled_at}")
        return job_id

    def cancel_scheduled_tweet(self, job_id: str):
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"Cancelled job {job_id}")
        except Exception as e:
            logger.warning(f"Could not cancel job {job_id}: {e}")

    def _send_scheduled_tweet(self, tweet_id: int):
        from app.database import SessionLocal
        from app.models.tweet import ScheduledTweet, TweetStatus, TweetLog
        from app.services.twitter_service import twitter_service
        from datetime import timezone

        db = SessionLocal()
        try:
            tweet = db.query(ScheduledTweet).filter(ScheduledTweet.id == tweet_id).first()
            if not tweet or tweet.status != TweetStatus.pending:
                return

            result = twitter_service.post_tweet(tweet.content)
            if result["success"]:
                tweet.status = TweetStatus.sent
                tweet.sent_at = datetime.now(timezone.utc)
                tweet.tweet_id = result["tweet_id"]
                log = TweetLog(
                    tweet_id=result["tweet_id"],
                    content=tweet.content,
                    source="scheduled",
                )
                db.add(log)
            else:
                tweet.status = TweetStatus.failed
                tweet.error_message = result.get("error")
            db.commit()
        finally:
            db.close()

    def _get_bot_settings(self, db):
        """Load bot settings from DB, creating defaults if needed."""
        from app.models.bot_settings import BotSettings
        s = db.query(BotSettings).first()
        if not s:
            s = BotSettings(id=1)
            db.add(s)
            db.commit()
            db.refresh(s)
        return s

    def _process_queue(self):
        from app.database import SessionLocal
        from app.models.tweet import TweetQueue, TweetStatus, TweetLog
        from app.services.twitter_service import twitter_service
        from datetime import timezone

        db = SessionLocal()
        try:
            bot_settings = self._get_bot_settings(db)
            if not bot_settings.bot_enabled:
                return

            # Check active hours
            now = datetime.now()
            if not (bot_settings.active_hours_start <= now.hour < bot_settings.active_hours_end):
                logger.debug(f"Outside active hours ({bot_settings.active_hours_start}-{bot_settings.active_hours_end}), skipping")
                return

            # Check daily limit
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            today_count = db.query(TweetQueue).filter(
                TweetQueue.status == TweetStatus.sent,
                TweetQueue.sent_at >= today_start,
            ).count()
            if today_count >= bot_settings.tweets_per_day:
                logger.debug(f"Daily limit reached ({today_count}/{bot_settings.tweets_per_day})")
                return

            # Random skip for human-like behavior
            import random
            if random.randint(1, 100) <= bot_settings.random_skip_chance:
                logger.debug("Random skip triggered")
                return

            next_tweet = (
                db.query(TweetQueue)
                .filter(TweetQueue.status == TweetStatus.pending)
                .order_by(TweetQueue.priority.desc(), TweetQueue.created_at)
                .first()
            )
            if not next_tweet:
                return

            result = twitter_service.post_tweet(next_tweet.content)
            if result["success"]:
                next_tweet.status = TweetStatus.sent
                next_tweet.sent_at = datetime.now(timezone.utc)
                next_tweet.tweet_id = result["tweet_id"]
                log = TweetLog(
                    tweet_id=result["tweet_id"],
                    content=next_tweet.content,
                    source="queue",
                )
                db.add(log)
            else:
                next_tweet.status = TweetStatus.failed
                next_tweet.error_message = result.get("error")
            db.commit()
        finally:
            db.close()

    def _check_mentions(self):
        if not settings.AUTO_REPLY_ENABLED:
            return

        from app.database import SessionLocal
        from app.models.auto_reply import AutoReplyRule
        from app.services.twitter_service import twitter_service
        from datetime import timezone

        db = SessionLocal()
        try:
            mentions = twitter_service.get_mentions()
            rules = db.query(AutoReplyRule).filter(AutoReplyRule.is_active.is_(True)).all()

            for mention in mentions:
                for rule in rules:
                    if self._matches_rule(mention.text, rule):
                        result = twitter_service.reply_to_tweet(
                            rule.reply_template, str(mention.id)
                        )
                        if result["success"]:
                            rule.trigger_count += 1
                            rule.last_triggered = datetime.now(timezone.utc)
                            db.commit()
                        break
        finally:
            db.close()

    def _matches_rule(self, text: str, rule) -> bool:
        text_lower = text.lower()
        keyword_lower = rule.keyword.lower()
        if rule.match_type == "exact":
            return text_lower == keyword_lower
        elif rule.match_type == "regex":
            return bool(re.search(rule.keyword, text, re.IGNORECASE))
        else:
            return keyword_lower in text_lower

    def _run_bot_cycle(self):
        """Run the FlippX autonomous bot cycle."""
        from app.services.twitter_service import twitter_service

        try:
            twitter_service.run_bot_cycle()
        except Exception as e:
            logger.error(f"Bot cycle failed: {e}")

    def _refill_queue(self):
        """Auto-generate tweets when queue drops below threshold."""
        from app.database import SessionLocal
        from app.models.tweet import TweetQueue, TweetStatus
        from app.services.twitter_service import twitter_service

        db = SessionLocal()
        try:
            bot_settings = self._get_bot_settings(db)
            if not bot_settings.bot_enabled or not bot_settings.auto_refill_enabled:
                return

            pending_count = db.query(TweetQueue).filter(
                TweetQueue.status == TweetStatus.pending
            ).count()

            if pending_count >= bot_settings.refill_threshold:
                logger.debug(f"Queue has {pending_count} pending tweets, no refill needed")
                return

            needed = bot_settings.refill_count - pending_count
            logger.info(f"Queue low ({pending_count} pending), generating {needed} tweets")
            tweets = twitter_service.generate_tweet_batch(needed)
            for text in tweets:
                db.add(TweetQueue(content=text, priority=0))
            db.commit()
            logger.info(f"Refilled queue with {len(tweets)} tweets")
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to refill queue: {e}")
        finally:
            db.close()

    def _sync_analytics(self):
        from app.database import SessionLocal
        from app.models.tweet import TweetLog
        from app.services.twitter_service import twitter_service

        db = SessionLocal()
        try:
            recent_logs = db.query(TweetLog).order_by(TweetLog.sent_at.desc()).limit(50).all()
            for log in recent_logs:
                metrics = twitter_service.get_tweet_metrics(log.tweet_id)
                if metrics:
                    log.likes = metrics.get("like_count", 0)
                    log.retweets = metrics.get("retweet_count", 0)
                    log.impressions = metrics.get("impression_count", 0)
                    log.replies = metrics.get("reply_count", 0)
            db.commit()
        finally:
            db.close()

    def get_jobs(self) -> list:
        return [
            {
                "id": job.id,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                "name": job.name,
            }
            for job in self.scheduler.get_jobs()
        ]


scheduler_service = SchedulerService()
