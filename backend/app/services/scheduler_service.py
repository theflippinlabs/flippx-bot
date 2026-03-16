from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from datetime import datetime
import logging
import random
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
        # Process queue every 5 minutes
        self.scheduler.add_job(
            self._process_queue,
            "interval",
            minutes=5,
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

    def _process_queue(self):
        from app.services.bot_state import is_bot_enabled
        if not is_bot_enabled():
            return

        from app.database import SessionLocal
        from app.models.tweet import TweetQueue, TweetStatus, TweetLog
        from app.services.twitter_service import twitter_service
        from datetime import timezone

        db = SessionLocal()
        try:
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
        from app.services.bot_state import is_auto_reply_enabled
        if not is_auto_reply_enabled():
            return

        from app.services.twitter_service import twitter_service
        import time

        try:
            mentions, includes = twitter_service.get_mentions()
            if not mentions:
                return

            # Build author lookup from includes
            users_by_id = {}
            if includes and "users" in includes:
                for user in includes["users"]:
                    users_by_id[str(user.id)] = user

            replied_count = 0
            for mention in mentions:
                tweet_id = str(mention.id)

                # Skip if already replied
                if twitter_service.is_already_interacted(tweet_id):
                    continue

                # Get author username
                author = users_by_id.get(str(mention.author_id))
                author_username = author.username if author else "someone"

                # Generate AI reply using Anthropic
                reply_text = twitter_service.generate_mention_reply(
                    mention.text, author_username
                )
                if not reply_text:
                    continue

                result = twitter_service.reply_to_tweet(reply_text, tweet_id)
                if result["success"]:
                    twitter_service.log_interaction(tweet_id, "replied")
                    replied_count += 1
                    logger.info(f"Auto-replied to @{author_username} mention ({tweet_id})")

                    # Human-like delay between replies
                    time.sleep(random.uniform(3, 8))

                # Cap at 5 auto-replies per check
                if replied_count >= 5:
                    break

            if replied_count > 0:
                logger.info(f"Auto-replied to {replied_count} mentions this check")
        except Exception as e:
            logger.error(f"Mention check failed: {e}")

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
