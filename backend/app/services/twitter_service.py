import tweepy
import random
import time
import logging
from datetime import datetime

from app.config import settings

logger = logging.getLogger(__name__)

SEARCH_QUERIES = [
    "Bitcoin", "Ethereum", "Solana", "DeFi", "crypto alpha",
    "Web3", "AI agents", "blockchain", "NFT", "memecoin",
    "Layer 2", "onchain", "tokenomics", "crypto trading",
    "AI startups", "GPU", "LLM", "tech IPO", "fintech",
    "smart contracts", "airdrop", "staking", "DEX",
]


class TwitterService:
    def __init__(self):
        self._client = None
        self._claude = None

    @property
    def client(self) -> tweepy.Client:
        if not self._client:
            # Support both TWITTER_API_KEY and TWITTER_CONSUMER_KEY
            consumer_key = settings.TWITTER_API_KEY or settings.TWITTER_CONSUMER_KEY

            if not all([
                consumer_key,
                settings.TWITTER_API_SECRET,
                settings.TWITTER_ACCESS_TOKEN,
                settings.TWITTER_ACCESS_TOKEN_SECRET,
            ]):
                missing = []
                if not consumer_key:
                    missing.append("TWITTER_API_KEY (or TWITTER_CONSUMER_KEY)")
                if not settings.TWITTER_API_SECRET:
                    missing.append("TWITTER_API_SECRET")
                if not settings.TWITTER_ACCESS_TOKEN:
                    missing.append("TWITTER_ACCESS_TOKEN")
                if not settings.TWITTER_ACCESS_TOKEN_SECRET:
                    missing.append("TWITTER_ACCESS_TOKEN_SECRET")
                logger.error(f"Twitter credentials missing: {', '.join(missing)}")

            self._client = tweepy.Client(
                consumer_key=consumer_key,
                consumer_secret=settings.TWITTER_API_SECRET,
                access_token=settings.TWITTER_ACCESS_TOKEN,
                access_token_secret=settings.TWITTER_ACCESS_TOKEN_SECRET,
                wait_on_rate_limit=True,
            )
        return self._client

    @property
    def bearer_client(self) -> tweepy.Client:
        """Separate client for read-only endpoints that use Bearer Token."""
        return tweepy.Client(
            bearer_token=settings.TWITTER_BEARER_TOKEN,
            wait_on_rate_limit=True,
        )

    @property
    def claude(self):
        if not self._claude:
            import anthropic
            self._claude = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        return self._claude

    # ── Existing methods (unchanged) ──────────────────────────────────

    def post_tweet(self, content: str) -> dict:
        try:
            response = self.client.create_tweet(text=content, user_auth=True)
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
                user_auth=True,
            )
            logger.info(f"Replied to {tweet_id}: {response.data['id']}")
            return {"success": True, "tweet_id": response.data["id"]}
        except tweepy.TweepyException as e:
            logger.error(f"Failed to reply: {e}")
            return {"success": False, "error": str(e)}

    def get_mentions(self, since_id: str = None) -> list:
        try:
            me = self.client.get_me(user_auth=True)
            params = {
                "expansions": ["author_id"],
                "tweet_fields": ["created_at", "text"],
                "user_fields": ["username"],
            }
            if since_id:
                params["since_id"] = since_id
            mentions = self.client.get_users_mentions(me.data.id, **params)
            return mentions.data or [], mentions.includes if mentions.includes else {}
        except tweepy.TweepyException as e:
            logger.error(f"Failed to get mentions: {e}")
            return [], {}

    def generate_mention_reply(self, tweet_text: str, author_username: str) -> str | None:
        """Use Claude to generate a smart contextual reply to a mention."""
        try:
            response = self.claude.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=300,
                messages=[{
                    "role": "user",
                    "content": (
                        f"@{author_username} mentioned you (@theflippinlabs) in this tweet:\n\n"
                        f'"{tweet_text}"\n\n'
                        "Write a reply that:\n"
                        "- Directly addresses what they said/asked\n"
                        "- Uses 2-3 emojis to keep the energy up\n"
                        "- Is helpful, witty, and encourages further conversation\n"
                        "- If they asked a question, answer it with insight\n"
                        "- If they tagged you for attention, acknowledge them and add value\n"
                        "- Under 250 characters\n"
                        "- Output ONLY the reply text. No quotes, no explanation."
                    ),
                }],
                system=settings.REPLY_PERSONA,
            )
            reply_text = response.content[0].text.strip().strip('"')
            if len(reply_text) > 280:
                reply_text = reply_text[:277] + "..."
            logger.info(f"Generated mention reply ({len(reply_text)} chars): {reply_text[:60]}...")
            return reply_text
        except Exception as e:
            logger.error(f"Failed to generate mention reply: {e}")
            return None

    def get_tweet_metrics(self, tweet_id: str) -> dict:
        try:
            tweet = self.bearer_client.get_tweet(
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
            me = self.client.get_me(user_fields=["public_metrics", "profile_image_url"], user_auth=True)
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
        """Search multiple crypto/tech queries to build a rich trending picture."""
        topics = []
        # Sample 3 different queries for diversity
        queries = random.sample(SEARCH_QUERIES, min(3, len(SEARCH_QUERIES)))
        for query in queries:
            try:
                results = self.bearer_client.search_recent_tweets(
                    query=f"{query} -is:retweet lang:en",
                    max_results=10,
                    tweet_fields=["public_metrics", "text"],
                )
                if results.data:
                    # Prioritize tweets with higher engagement
                    sorted_tweets = sorted(
                        results.data,
                        key=lambda t: (t.public_metrics or {}).get("like_count", 0),
                        reverse=True,
                    )
                    for tweet in sorted_tweets[:5]:
                        topics.append(tweet.text)
                logger.info(f"Fetched tweets for topic: {query}")
            except tweepy.TweepyException as e:
                logger.error(f"Failed to fetch trending topics for '{query}': {e}")
        logger.info(f"Total trending topics collected: {len(topics)}")
        return topics

    def generate_tweet(self, topics: list[str]) -> str | None:
        """Use Claude to generate a full 280-char tweet with emojis, hashtags, and tags."""
        if not topics:
            topic_context = "Current crypto and tech trends: Bitcoin, Ethereum, Solana, AI agents, DeFi, Web3, Layer 2s, memecoins"
        else:
            topic_context = "\n".join(topics[:15])

        try:
            response = self.claude.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=400,
                messages=[{
                    "role": "user",
                    "content": (
                        f"Here are trending crypto/tech tweets right now:\n\n{topic_context}\n\n"
                        "Write ONE original tweet that will go viral. Requirements:\n"
                        "- USE ALL 280 CHARACTERS. Aim for 250-280 chars. Short tweets get no reach.\n"
                        "- Include 3-5 emojis spread throughout the tweet.\n"
                        "- Include 2-3 relevant hashtags like #Bitcoin #Crypto #AI #Web3 #DeFi #Solana #ETH.\n"
                        "- Tag 1-2 relevant influential accounts IF discussing their projects "
                        "(e.g. @VitalikButerin for ETH, @elonmusk for tech/AI, @CZ_Binance for Binance, "
                        "@brian_armstrong for Coinbase, @jessepollak for Base, @aaboronkov for crypto analysis). "
                        "Only tag when genuinely relevant to the topic.\n"
                        "- Make it a hot take, alpha call, or conversation starter that people want to reply to.\n"
                        "- Don't copy the tweets above — use them to identify what's trending and craft your own take.\n"
                        "- Output ONLY the tweet text. No quotes, no explanation."
                    ),
                }],
                system=settings.BOT_PERSONA,
            )
            tweet_text = response.content[0].text.strip().strip('"')
            if len(tweet_text) > 280:
                tweet_text = tweet_text[:277] + "..."
            logger.info(f"Generated tweet ({len(tweet_text)} chars): {tweet_text[:80]}...")
            return tweet_text
        except Exception as e:
            logger.error(f"Failed to generate tweet with Claude: {e}")
            return None

    def generate_reply(self, tweet_text: str, author_username: str) -> str | None:
        """Use Claude to generate a smart contextual reply with emojis."""
        try:
            response = self.claude.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=300,
                messages=[{
                    "role": "user",
                    "content": (
                        f"Reply to this tweet by @{author_username}:\n\n"
                        f'"{tweet_text}"\n\n'
                        "Write ONE reply that:\n"
                        "- Uses 2-3 emojis to stand out in the replies\n"
                        "- Adds genuine insight, alpha, or a spicy counter-take\n"
                        "- Asks a follow-up question OR drops knowledge to keep the thread alive\n"
                        "- Is under 250 characters\n"
                        "- Output ONLY the reply text. No quotes, no explanation."
                    ),
                }],
                system=settings.REPLY_PERSONA,
            )
            reply_text = response.content[0].text.strip().strip('"')
            if len(reply_text) > 280:
                reply_text = reply_text[:277] + "..."
            logger.info(f"Generated reply ({len(reply_text)} chars): {reply_text[:60]}...")
            return reply_text
        except Exception as e:
            logger.error(f"Failed to generate reply with Claude: {e}")
            return None

    def search_timeline_tweets(self) -> list:
        """Fetch recent popular crypto/tech tweets for engagement."""
        try:
            query = random.choice(SEARCH_QUERIES) + " -is:retweet -is:reply lang:en"
            results = self.bearer_client.search_recent_tweets(
                query=query,
                max_results=10,
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

    def run_bot_cycle(self):
        """Main bot cycle: generate tweet, reply, like, retweet."""
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
            if replies_sent >= settings.REPLIES_PER_RUN:
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

        likes_done = 0
        for tweet in like_candidates:
            if likes_done >= settings.LIKES_PER_RUN:
                break

            if self.like_tweet(tweet["id"]):
                self.log_interaction(tweet["id"], "liked")
                likes_done += 1
                self._random_delay()

        logger.info(f"Liked {likes_done} tweets this cycle")

    def _step_retweet(self, timeline: list):
        """Retweet tweets with 50+ likes that haven't been interacted with."""
        rt_candidates = [
            t for t in timeline
            if t["metrics"].get("like_count", 0) >= 50
            and not self.is_already_interacted(t["id"])
        ]
        random.shuffle(rt_candidates)

        if not rt_candidates:
            logger.info("No retweet candidates with 50+ likes")
            return

        rts_done = 0
        for tweet in rt_candidates:
            if rts_done >= settings.RETWEETS_PER_RUN:
                break
            if self.retweet(tweet["id"]):
                self.log_interaction(tweet["id"], "retweeted")
                rts_done += 1
                logger.info(f"Retweeted {tweet['id']} ({tweet['metrics'].get('like_count', 0)} likes)")
                if rts_done < settings.RETWEETS_PER_RUN:
                    self._random_delay()

        logger.info(f"Retweeted {rts_done} tweets this cycle")


twitter_service = TwitterService()
