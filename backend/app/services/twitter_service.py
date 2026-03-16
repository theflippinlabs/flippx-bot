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

# CRO/Cronos community engagement queries
CRO_SEARCH_QUERIES = [
    "from:cronos_chain", "from:cryptocom", "#CroFam",
    "$CRO cronos", "Cronos chain", "crypto.com CRO",
    "#CRO", "Cronos DeFi",
]

TOPIC_CATEGORIES = [
    "Bitcoin price action and macro outlook",
    "Ethereum ecosystem and upgrades",
    "Solana speed, DeFi, and memecoins",
    "AI agents and autonomous systems in crypto",
    "DeFi yield strategies and protocol wars",
    "Layer 2 scaling wars (Arbitrum vs Optimism vs Base vs zkSync)",
    "Crypto regulation and government moves",
    "NFT market evolution and digital art",
    "Real World Assets (RWA) tokenization",
    "Stablecoin dominance and CBDC threats",
    "Crypto VC funding and startup landscape",
    "AI x Crypto intersection projects",
    "Memecoins and degen culture",
    "On-chain analytics and whale watching",
    "Tech industry layoffs, pivots, and AI hiring",
    "GPU shortage and AI infrastructure",
    "Open source AI vs closed models debate",
    "Web3 gaming and metaverse",
    "Cross-chain bridges and interoperability",
    "Crypto exchange competition and drama",
    "Cronos ecosystem, $CRO staking, and Crypto.com growth",
    "CRO DeFi on Cronos chain — VVS, Tectonic, Ferro",
]


class TwitterService:
    def __init__(self):
        self._client = None
        self._claude = None
        self._last_topics: list[str] = []  # Track recent topics to avoid repeats

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
            mentions = self.bearer_client.get_users_mentions(me.data.id, **params)
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

    def _pick_topic_category(self) -> str:
        """Pick a topic category that wasn't used recently."""
        available = [t for t in TOPIC_CATEGORIES if t not in self._last_topics]
        if not available:
            self._last_topics.clear()
            available = TOPIC_CATEGORIES
        chosen = random.choice(available)
        self._last_topics.append(chosen)
        # Keep only last 5 to ensure variety
        if len(self._last_topics) > 5:
            self._last_topics = self._last_topics[-5:]
        return chosen

    def generate_tweet(self, topics: list[str]) -> str | None:
        """Use Claude to generate a full 280-char tweet with emojis, hashtags, and tags."""
        topic_category = self._pick_topic_category()

        if not topics:
            trend_context = "No specific trending tweets available — use your knowledge of current crypto/tech landscape."
        else:
            trend_context = "\n".join(f"- {t}" for t in topics[:12])

        # Pick a random tweet style to force variety
        styles = [
            "Witty observation — point out something obvious that nobody talks about",
            "Contrarian take — challenge something everyone assumes is true",
            "Relatable analogy — explain a crypto/tech concept through an everyday comparison",
            "Specific market insight — mention concrete numbers, projects, or trends",
            "Self-aware humor about the industry or community",
            "Prediction with reasoning — what's coming next and why",
            "Comparison that reframes how people think about two things",
            "Question that makes people stop scrolling and think",
        ]
        chosen_style = random.choice(styles)

        # 50/50 short punchy vs long detailed
        length_modes = [
            ("SHORT", "80-140 characters. Punchy one-liner. Sharp and memorable. Like a mic drop."),
            ("LONG", "240-280 characters. Detailed take with reasoning, analogy, or multi-part observation."),
        ]
        length_mode, length_instruction = random.choice(length_modes)

        try:
            response = self.claude.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=400,
                messages=[{
                    "role": "user",
                    "content": (
                        f"TOPIC: {topic_category}\n"
                        f"STYLE: {chosen_style}\n"
                        f"LENGTH MODE: {length_mode}\n\n"
                        f"Trending tweets for context:\n{trend_context}\n\n"
                        "Write ONE tweet as @theflippinlabs. STRICT requirements:\n\n"
                        f"1. LENGTH: {length_instruction} "
                        "Count carefully. Do NOT exceed 280 characters total.\n\n"
                        "2. EMOJIS: 1-3 emojis placed naturally MID-SENTENCE. "
                        "GOOD: 'The 🔥 thing about $SOL is that...' or 'Everyone's sleeping on this 👀 while...' "
                        "BAD: 'Solana is amazing 🔥🚀💎' (never cluster at end).\n\n"
                        "3. HASHTAGS: End with 1-3 hashtags. Choose from: "
                        "#Bitcoin #Crypto #AI #Web3 #DeFi #Solana #ETH #BTC #Tech #Trading #Blockchain #Layer2 "
                        "#CRO #Cronos #CroFam\n\n"
                        "4. SPECIFICS: Use $tokens ($BTC $ETH $SOL $CRO $AVAX $ARB $OP $LINK) or "
                        "@accounts (@VitalikButerin @elonmusk @CZ_Binance @brian_armstrong @jessepollak @pmarca "
                        "@cronos_chain @cryptocom) when they naturally fit. Don't force them.\n\n"
                        "5. TONE: Dry wit + real knowledge. Think smart friend, not hype account. "
                        "Use analogies and specific observations. NEVER use: 'alpha', 'WAGMI', 'NFA', "
                        "'let that sink in', 'hear me out', 'not financial advice', 'bullish on', "
                        "'few understand this'.\n\n"
                        "Output ONLY the tweet. No quotes. No preamble."
                    ),
                }],
                system=settings.BOT_PERSONA,
            )
            tweet_text = response.content[0].text.strip().strip('"')
            # Strip any preamble like "Here's..." or "Tweet:" that models sometimes add
            for prefix in ["Here's a tweet:", "Here's my tweet:", "Tweet:", "Here you go:"]:
                if tweet_text.lower().startswith(prefix.lower()):
                    tweet_text = tweet_text[len(prefix):].strip()
            if len(tweet_text) > 280:
                tweet_text = tweet_text[:277] + "..."
            logger.info(
                f"Generated tweet ({len(tweet_text)} chars) "
                f"[topic={topic_category[:30]}] [style={chosen_style[:30]}]: "
                f"{tweet_text[:80]}..."
            )
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

    def search_cro_community_tweets(self) -> list:
        """Fetch recent tweets from @cronos_chain, @cryptocom, and #CroFam community."""
        all_tweets = []
        queries = random.sample(CRO_SEARCH_QUERIES, min(3, len(CRO_SEARCH_QUERIES)))
        for query in queries:
            try:
                results = self.bearer_client.search_recent_tweets(
                    query=f"{query} -is:retweet lang:en",
                    max_results=10,
                    tweet_fields=["public_metrics", "created_at", "author_id", "text"],
                    expansions=["author_id"],
                    user_fields=["public_metrics", "username"],
                )
                users_by_id = {}
                if results.includes and "users" in results.includes:
                    for user in results.includes["users"]:
                        users_by_id[str(user.id)] = user

                if results.data:
                    for tweet in results.data:
                        author = users_by_id.get(str(tweet.author_id))
                        all_tweets.append({
                            "id": str(tweet.id),
                            "text": tweet.text,
                            "metrics": tweet.public_metrics or {},
                            "author_id": str(tweet.author_id),
                            "author_username": author.username if author else "unknown",
                            "author_followers": (
                                author.public_metrics.get("followers_count", 0) if author else 0
                            ),
                        })
            except tweepy.TweepyException as e:
                logger.error(f"Failed to search CRO tweets for '{query}': {e}")
        logger.info(f"Found {len(all_tweets)} CRO/Cronos community tweets")
        return all_tweets

    def generate_supportive_reply(self, tweet_text: str, author_username: str) -> str | None:
        """Generate a positive, supportive reply for CRO/Cronos community tweets."""
        try:
            response = self.claude.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=300,
                messages=[{
                    "role": "user",
                    "content": (
                        f"Reply to this tweet by @{author_username}:\n\n"
                        f'"{tweet_text}"\n\n'
                        "Write ONE supportive reply that:\n"
                        "- Is genuinely positive and encouraging about the Cronos/$CRO ecosystem\n"
                        "- Uses 2-3 emojis naturally\n"
                        "- Adds value: mention a specific feature, stat, or reason you're excited\n"
                        "- Sounds authentic, not like a shill bot\n"
                        "- Under 200 characters\n"
                        "- Output ONLY the reply. No quotes."
                    ),
                }],
                system=(
                    "You are @theflippinlabs, a crypto enthusiast who genuinely supports the "
                    "Cronos ecosystem and $CRO. You're positive but authentic — never over-the-top "
                    "or fake. You add real observations and excitement."
                ),
            )
            reply_text = response.content[0].text.strip().strip('"')
            if len(reply_text) > 280:
                reply_text = reply_text[:277] + "..."
            return reply_text
        except Exception as e:
            logger.error(f"Failed to generate supportive reply: {e}")
            return None

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
        """Main bot cycle: generate tweet, engage CRO community, engage trending."""
        # Active hours check (7AM - 11PM)
        current_hour = datetime.now().hour
        if current_hour < 7 or current_hour >= 23:
            logger.info("Outside active hours (7AM-11PM), skipping cycle")
            return

        # 15% random skip for human-like behavior
        if random.random() < 0.15:
            logger.info("Random skip triggered (15% chance), skipping cycle")
            return

        from app.services.bot_state import is_bot_enabled
        if not is_bot_enabled():
            logger.info("Bot is disabled, skipping cycle")
            return

        logger.info("=== Starting FlippX bot cycle ===")

        # 1. Generate and post an AI tweet
        self._step_post_ai_tweet()
        self._random_delay()

        # 2. CRO/Cronos community engagement (like, retweet, reply)
        cro_tweets = self.search_cro_community_tweets()
        if cro_tweets:
            self._step_cro_engagement(cro_tweets)
            self._random_delay()

        # 3. Fetch trending crypto/tech timeline for general engagement
        timeline = self.search_timeline_tweets()
        if timeline:
            # 4. Reply to up to 3 tweets (1000+ follower accounts only)
            self._step_reply_to_tweets(timeline)
            self._random_delay()

            # 5. Like 3-5 tweets
            self._step_like_tweets(timeline)
            self._random_delay()

            # 6. Retweet 1 tweet with 50+ likes
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

    def _step_cro_engagement(self, cro_tweets: list):
        """Like, retweet, and reply to CRO/Cronos community tweets with positive tone."""
        logger.info(f"Starting CRO community engagement with {len(cro_tweets)} tweets")

        # Prioritize @cronos_chain and @cryptocom tweets
        priority_tweets = [
            t for t in cro_tweets
            if t["author_username"].lower() in ("cronos_chain", "cryptocom")
            and not self.is_already_interacted(t["id"])
        ]
        community_tweets = [
            t for t in cro_tweets
            if t["author_username"].lower() not in ("cronos_chain", "cryptocom")
            and not self.is_already_interacted(t["id"])
        ]

        # Like all priority tweets + up to 5 community tweets
        liked = 0
        for tweet in priority_tweets:
            if self.like_tweet(tweet["id"]):
                self.log_interaction(tweet["id"], "liked")
                liked += 1
                self._random_delay()

        random.shuffle(community_tweets)
        for tweet in community_tweets[:5]:
            if self.like_tweet(tweet["id"]):
                self.log_interaction(tweet["id"], "liked")
                liked += 1
                self._random_delay()

        # Retweet up to 2 priority tweets
        rts = 0
        for tweet in priority_tweets[:2]:
            if self.retweet(tweet["id"]):
                self.log_interaction(tweet["id"], "retweeted")
                rts += 1
                self._random_delay()

        # Reply to up to 3 CRO tweets (priority first, then community)
        reply_pool = priority_tweets[:2] + community_tweets[:3]
        random.shuffle(reply_pool)
        replies = 0
        for tweet in reply_pool:
            if replies >= 3:
                break
            reply_text = self.generate_supportive_reply(tweet["text"], tweet["author_username"])
            if not reply_text:
                continue
            result = self.reply_to_tweet(reply_text, tweet["id"])
            if result["success"]:
                self.log_interaction(tweet["id"], "replied")
                replies += 1
                self._random_delay()

        logger.info(
            f"CRO engagement: {liked} likes, {rts} retweets, {replies} replies"
        )


twitter_service = TwitterService()
