import tweepy
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class TwitterService:
    def __init__(self):
        self._client = None
        self._api = None

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


twitter_service = TwitterService()
