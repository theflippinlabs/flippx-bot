import tweepy
import random
import time
import logging
from datetime import datetime

from app.config import settings

logger = logging.getLogger(__name__)

FALLBACK_TWEET_PERSONA = (
    "Confident, sharp, slightly provocative but always credible. "
    "Natural conversational English like a real Twitter power user. "
    "Mix of short punchy takes, bold statements, questions to the audience. "
    "1-3 emojis max per tweet, sometimes none. Never use markdown, dashes, or special characters."
)

FALLBACK_REPLY_PERSONA = (
    "Engaging, smart, adds value to the conversation. Short and punchy. "
    "Never sycophantic. Feels like a real human reply, not a bot."
)

MENTION_INSTRUCTION = (
    "IMPORTANT: For approximately 50% of tweets, naturally mention/tag 1-2 relevant well-known accounts "
    "using @username. Only tag accounts that are genuinely relevant to the tweet topic "
    "(e.g. @elonmusk for Tesla/SpaceX/X topics, @VitalikButerin for Ethereum, @naval for startups, "
    "@balaborealismo for AI art, @sama for OpenAI, @CoinDesk for crypto news, @aaborealismo, etc). "
    "The mention must feel natural — never forced. Max 1-2 tags per tweet."
)


def _get_personas() -> tuple[str, str]:
    """Load personas from database, fall back to defaults."""
    try:
        from app.database import SessionLocal
        from app.models.bot_settings import BotSettings
        db = SessionLocal()
        s = db.query(BotSettings).filter(BotSettings.id == 1).first()
        db.close()
        if s:
            return (s.tweet_persona or FALLBACK_TWEET_PERSONA, s.reply_persona or FALLBACK_REPLY_PERSONA)
    except Exception:
        pass
    return (FALLBACK_TWEET_PERSONA, FALLBACK_REPLY_PERSONA)

SEARCH_QUERIES = [
    "tech", "AI", "startups", "programming", "science",
    "culture", "finance", "crypto", "design", "productivity",
]


class TwitterService:
    def __init__(self):
        self._client = None
        self._claude = None

    @property
    def client(self) -> tweepy.Client:
        if not self._client:
            self._client = tweepy.Client(
                bearer_token=settings.TWITTER_BEARER_TOKEN,
                consumer_key=settings.TWITTER_API_KEY,
                consumer_secret=settings.TWITTER_API_SECRET,
                access_token=settings.TWITTER_ACCESS_TOKEN,
                access_token_secret=settings.TWITTER_ACCESS_TOKEN_SECRET,
            )
        return self._client

    @property
    def claude(self):
        if not self._claude:
            import anthropic
            self._claude = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        return self._claude

    # ── Existing methods (unchanged) ──────────────────────────────────

    def post_tweet(self, content: str) -> dict:
        try:
            response = self.client.create_tweet(text=content)
            tweet_id = response.data["id"]
            logger.info(f"Tweet posted: {tweet_id}")
            return {"success": True, "tweet_id": tweet_id}
        except tweepy.TweepyException as e:
            logger.error(f"Failed to post tweet: {e}")
            return {"success": False, "error": str(e)}

    def reply_to_tweet(self, content: str, tweet_id: str) -> dict:
        try:
            response = self.client.create_tweet(
                text=content,
                in_reply_to_tweet_id=tweet_id,
            )
            logger.info(f"Replied to {tweet_id}: {response.data['id']}")
            return {"success": True, "tweet_id": response.data["id"]}
        except tweepy.TweepyException as e:
            logger.error(f"Failed to reply: {e}")
            return {"success": False, "error": str(e)}

    def get_mentions(self, since_id: str = None) -> list:
        try:
            me = self.client.get_me()
            params = {"expansions": ["author_id"], "tweet_fields": ["created_at", "text"]}
            if since_id:
                params["since_id"] = since_id
            mentions = self.client.get_users_mentions(me.data.id, **params)
            return mentions.data or []
        except tweepy.TweepyException as e:
            logger.error(f"Failed to get mentions: {e}")
            return []

    def get_tweet_metrics(self, tweet_id: str) -> dict:
        try:
            tweet = self.client.get_tweet(
                tweet_id,
                tweet_fields=["public_metrics", "created_at"],
            )
            if tweet.data:
                return tweet.data.public_metrics or {}
            return {}
        except tweepy.TweepyException as e:
            logger.error(f"Failed to get metrics for {tweet_id}: {e}")
            return {}

    def get_me(self) -> dict:
        try:
            me = self.client.get_me(user_fields=["public_metrics", "profile_image_url"])
            metrics = me.data.public_metrics or {}
            return {
                "id": str(me.data.id),
                "name": me.data.name,
                "username": me.data.username,
                "metrics": {
                    "followers_count": metrics.get("followers_count", 0),
                    "following_count": metrics.get("following_count", 0),
                    "tweet_count": metrics.get("tweet_count", 0),
                },
            }
        except tweepy.TweepyException as e:
            logger.error(f"Failed to get user info: {e}")
            return {}

    # ── New: AI-powered methods ───────────────────────────────────────

    def fetch_trending_topics(self) -> list[str]:
        """Search recent popular tweets to extract trending topics."""
        topics = []
        query = random.choice(SEARCH_QUERIES)
        try:
            results = self.client.search_recent_tweets(
                query=query,
                max_results=20,
                sort_order="relevancy",
                tweet_fields=["public_metrics", "text"],
            )
            if results.data:
                for tweet in results.data:
                    topics.append(tweet.text)
            logger.info(f"Fetched {len(topics)} tweets for topic discovery (query: {query})")
        except tweepy.TweepyException as e:
            logger.error(f"Failed to fetch trending topics: {e}")
        return topics

    def generate_tweet(self, topics: list[str]) -> str | None:
        """Use Claude to generate an original tweet based on trending topics."""
        if not topics:
            topic_context = "current internet culture and tech trends"
        else:
            topic_context = "\n".join(topics[:10])

        tweet_persona, _ = _get_personas()
        try:
            response = self.claude.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=300,
                messages=[{
                    "role": "user",
                    "content": (
                        f"Here are some trending tweets for inspiration:\n\n{topic_context}\n\n"
                        "Write ONE original tweet. Don't copy or reference the tweets above directly — "
                        "use them only to understand what topics are hot right now. "
                        "Be original and have your own take.\n\n"
                        f"{MENTION_INSTRUCTION}"
                    ),
                }],
                system=tweet_persona,
            )
            tweet_text = response.content[0].text.strip().strip('"')
            if len(tweet_text) > 280:
                tweet_text = tweet_text[:277] + "..."
            logger.info(f"Generated tweet: {tweet_text[:50]}...")
            return tweet_text
        except Exception as e:
            logger.error(f"Failed to generate tweet with Claude: {e}")
            return None

    def generate_tweet_batch(self, count: int = 10) -> list[str]:
        """Generate a batch of unique AI tweets for the queue."""
        topics = self.fetch_trending_topics()
        if not topics:
            topic_context = "current internet culture and tech trends"
        else:
            topic_context = "\n".join(topics[:10])

        tweet_persona, _ = _get_personas()
        tweets = []
        # Generate in batches of 10 to reduce API calls
        remaining = count
        while remaining > 0:
            batch_size = min(remaining, 10)
            try:
                response = self.claude.messages.create(
                    model="claude-sonnet-4-6",
                    max_tokens=4000,
                    messages=[{
                        "role": "user",
                        "content": (
                            f"Here are some trending tweets for inspiration:\n\n{topic_context}\n\n"
                            f"Write exactly {batch_size} original tweets, each on its own line. "
                            "Number them 1. 2. 3. etc. "
                            "Don't copy or reference the tweets above directly — "
                            "use them only to understand what topics are hot right now. "
                            "Each tweet must be unique in topic and angle. "
                            "Mix styles: hot takes, observations, jokes, questions, mini-stories. "
                            "Every tweet MUST be under 280 characters.\n\n"
                            f"{MENTION_INSTRUCTION}"
                        ),
                    }],
                    system=tweet_persona,
                )
                raw = response.content[0].text.strip()
                for line in raw.split("\n"):
                    line = line.strip()
                    if not line:
                        continue
                    # Strip numbering like "1. " or "1) "
                    import re
                    cleaned = re.sub(r"^\d+[\.\)]\s*", "", line).strip().strip('"')
                    if cleaned and len(cleaned) <= 280:
                        tweets.append(cleaned)
                remaining -= batch_size
                logger.info(f"Generated batch, total tweets so far: {len(tweets)}")
            except Exception as e:
                logger.error(f"Failed to generate tweet batch: {e}")
                break

            # Brief delay between batches to avoid rate limits
            if remaining > 0:
                time.sleep(1)

        return tweets[:count]

    def generate_reply(self, tweet_text: str, author_username: str) -> str | None:
        """Use Claude to generate an intelligent reply to a tweet."""
        _, reply_persona = _get_personas()
        try:
            response = self.claude.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=200,
                messages=[{
                    "role": "user",
                    "content": (
                        f"Reply to this tweet by @{author_username}:\n\n"
                        f'"{tweet_text}"\n\n'
                        "Write ONE reply."
                    ),
                }],
                system=reply_persona,
            )
            reply_text = response.content[0].text.strip().strip('"')
            if len(reply_text) > 200:
                reply_text = reply_text[:197] + "..."
            logger.info(f"Generated reply: {reply_text[:50]}...")
            return reply_text
        except Exception as e:
            logger.error(f"Failed to generate reply with Claude: {e}")
            return None

    def search_timeline_tweets(self) -> list:
        """Fetch recent popular tweets from the timeline for engagement."""
        try:
            query = random.choice(SEARCH_QUERIES) + " -is:retweet -is:reply lang:en"
            results = self.client.search_recent_tweets(
                query=query,
                max_results=30,
                sort_order="relevancy",
                tweet_fields=["public_metrics", "created_at", "author_id", "text"],
                expansions=["author_id"],
                user_fields=["public_metrics", "username"],
            )
            tweets = []
            # Build author lookup
            users_by_id = {}
            if results.includes and "users" in results.includes:
                for user in results.includes["users"]:
                    users_by_id[str(user.id)] = user

            if results.data:
                for tweet in results.data:
                    author = users_by_id.get(str(tweet.author_id))
                    tweets.append({
                        "id": str(tweet.id),
                        "text": tweet.text,
                        "metrics": tweet.public_metrics or {},
                        "author_id": str(tweet.author_id),
                        "author_username": author.username if author else "unknown",
                        "author_followers": (
                            author.public_metrics.get("followers_count", 0) if author else 0
                        ),
                    })
            logger.info(f"Found {len(tweets)} timeline tweets for engagement")
            return tweets
        except tweepy.TweepyException as e:
            logger.error(f"Failed to search timeline: {e}")
            return []

    def like_tweet(self, tweet_id: str) -> bool:
        """Like a tweet by ID."""
        try:
            self.client.like(tweet_id=tweet_id, user_auth=True)
            logger.info(f"Liked tweet {tweet_id}")
            return True
        except tweepy.TweepyException as e:
            logger.error(f"Failed to like tweet {tweet_id}: {e}")
            return False

    def retweet(self, tweet_id: str) -> bool:
        """Retweet a tweet by ID."""
        try:
            self.client.retweet(tweet_id=tweet_id, user_auth=True)
            logger.info(f"Retweeted {tweet_id}")
            return True
        except tweepy.TweepyException as e:
            logger.error(f"Failed to retweet {tweet_id}: {e}")
            return False

    # ── Interaction tracking ──────────────────────────────────────────

    def is_already_interacted(self, tweet_id: str) -> bool:
        """Check if we've already interacted with this tweet."""
        from app.database import SessionLocal
        from app.models.tweet import InteractionLog

        db = SessionLocal()
        try:
            exists = db.query(InteractionLog).filter(
                InteractionLog.tweet_id == tweet_id
            ).first()
            return exists is not None
        finally:
            db.close()

    def log_interaction(self, tweet_id: str, interaction_type: str):
        """Record an interaction to prevent duplicates."""
        from app.database import SessionLocal
        from app.models.tweet import InteractionLog, InteractionType

        db = SessionLocal()
        try:
            log = InteractionLog(
                tweet_id=tweet_id,
                interaction_type=InteractionType(interaction_type),
            )
            db.add(log)
            db.commit()
        except Exception as e:
            db.rollback()
            logger.warning(f"Failed to log interaction for {tweet_id}: {e}")
        finally:
            db.close()

    # ── Main bot cycle ────────────────────────────────────────────────

    def _random_delay(self):
        """Human-like delay between actions."""
        delay = random.uniform(2, 8)
        logger.debug(f"Waiting {delay:.1f}s...")
        time.sleep(delay)

    def run_bot_cycle(self, manual: bool = False):
        """Main bot cycle: generate tweet, reply, like, retweet."""
        if not manual:
            # Active hours check (7AM - 11PM)
            current_hour = datetime.now().hour
            if current_hour < 7 or current_hour >= 23:
                logger.info("Outside active hours (7AM-11PM), skipping cycle")
                return

            # 15% random skip for human-like behavior
            if random.random() < 0.15:
                logger.info("Random skip triggered (15% chance), skipping cycle")
                return

        if not settings.BOT_ENABLED:
            logger.info("Bot is disabled, skipping cycle")
            return

        logger.info("=== Starting FlippX bot cycle ===")

        # 1. Generate and post an AI tweet
        self._step_post_ai_tweet()
        self._random_delay()

        # 2. Fetch timeline for engagement
        timeline = self.search_timeline_tweets()
        if not timeline:
            logger.warning("No timeline tweets found, ending cycle")
            return

        self._random_delay()

        # 3. Reply to up to 3 tweets (1000+ follower accounts only)
        self._step_reply_to_tweets(timeline)
        self._random_delay()

        # 4. Like 3-5 tweets
        self._step_like_tweets(timeline)
        self._random_delay()

        # 5. Retweet 1 tweet with 50+ likes
        self._step_retweet(timeline)

        logger.info("=== FlippX bot cycle complete ===")

    def _step_post_ai_tweet(self):
        """Generate and post one AI tweet."""
        topics = self.fetch_trending_topics()
        tweet_text = self.generate_tweet(topics)
        if not tweet_text:
            logger.warning("Could not generate tweet, skipping post")
            return

        result = self.post_tweet(tweet_text)
        if result["success"]:
            self.log_interaction(result["tweet_id"], "posted")
            # Log to TweetLog for analytics
            from app.database import SessionLocal
            from app.models.tweet import TweetLog
            db = SessionLocal()
            try:
                log = TweetLog(
                    tweet_id=result["tweet_id"],
                    content=tweet_text,
                    source="bot",
                )
                db.add(log)
                db.commit()
            finally:
                db.close()
            logger.info(f"Posted AI tweet: {result['tweet_id']}")

    def _step_reply_to_tweets(self, timeline: list):
        """Reply to up to 3 tweets from accounts with 1000+ followers."""
        reply_candidates = [
            t for t in timeline
            if t["author_followers"] >= 1000
            and not self.is_already_interacted(t["id"])
        ]
        random.shuffle(reply_candidates)

        replies_sent = 0
        for tweet in reply_candidates:
            if replies_sent >= 3:
                break

            reply_text = self.generate_reply(tweet["text"], tweet["author_username"])
            if not reply_text:
                continue

            result = self.reply_to_tweet(reply_text, tweet["id"])
            if result["success"]:
                self.log_interaction(tweet["id"], "replied")
                replies_sent += 1
                logger.info(f"Replied to @{tweet['author_username']} ({tweet['id']})")
                self._random_delay()

        logger.info(f"Sent {replies_sent} replies this cycle")

    def _step_like_tweets(self, timeline: list):
        """Like 3-5 random tweets that haven't been interacted with."""
        like_candidates = [
            t for t in timeline
            if not self.is_already_interacted(t["id"])
        ]
        random.shuffle(like_candidates)

        num_likes = random.randint(3, 5)
        likes_done = 0
        for tweet in like_candidates:
            if likes_done >= num_likes:
                break

            if self.like_tweet(tweet["id"]):
                self.log_interaction(tweet["id"], "liked")
                likes_done += 1
                self._random_delay()

        logger.info(f"Liked {likes_done} tweets this cycle")

    def _step_retweet(self, timeline: list):
        """Retweet 1 tweet from accounts with 10k+ followers that hasn't been interacted with."""
        # Load min followers from DB settings (default 10000)
        min_followers = 10000
        min_likes = 50
        try:
            from app.database import SessionLocal
            from app.models.bot_settings import BotSettings
            db = SessionLocal()
            s = db.query(BotSettings).filter(BotSettings.id == 1).first()
            if s:
                min_followers = getattr(s, 'min_followers_to_retweet', 10000) or 10000
                min_likes = s.min_likes_to_retweet or 50
            db.close()
        except Exception:
            pass

        rt_candidates = [
            t for t in timeline
            if t["metrics"].get("like_count", 0) >= min_likes
            and t.get("author_followers", 0) >= min_followers
            and not self.is_already_interacted(t["id"])
        ]
        random.shuffle(rt_candidates)

        if not rt_candidates:
            logger.info(f"No retweet candidates with {min_likes}+ likes and {min_followers}+ followers")
            return

        tweet = rt_candidates[0]
        if self.retweet(tweet["id"]):
            self.log_interaction(tweet["id"], "retweeted")
            logger.info(f"Retweeted {tweet['id']} ({tweet['metrics'].get('like_count', 0)} likes)")


twitter_service = TwitterService()
