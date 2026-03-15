from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Twitter API v2
    TWITTER_API_KEY: str = ""
    TWITTER_API_SECRET: str = ""
    TWITTER_ACCESS_TOKEN: str = ""
    TWITTER_ACCESS_TOKEN_SECRET: str = ""
    TWITTER_BEARER_TOKEN: str = ""

    # Anthropic (Claude AI)
    ANTHROPIC_API_KEY: str = ""

    # App
    DATABASE_URL: str = "sqlite:///./twitter_bot.db"
    SECRET_KEY: str = "change-me-in-production"
    API_KEY: str = "your-dashboard-api-key"  # Simple auth for the dashboard

    # Bot settings
    BOT_ENABLED: bool = True
    AUTO_REPLY_ENABLED: bool = True
    TWEET_INTERVAL_MINUTES: int = 60
    REPLIES_PER_RUN: int = 3
    LIKES_PER_RUN: int = 5
    RETWEETS_PER_RUN: int = 1

    # Bot personas
    BOT_PERSONA: str = (
        "You are a Twitter personality. Your style: sharp, witty, conversational. "
        "Mix humor with insight. No hashtags, no cringe, no generic motivational fluff. "
        "Sound like a smart friend, not a LinkedIn influencer. Max 1-2 emojis. "
        "Every tweet MUST be under 280 characters. Just output the tweet text, nothing else."
    )
    REPLY_PERSONA: str = (
        "You are replying to a tweet. Your style: genuinely engaging, add value, match the energy. "
        "Never sycophantic — never say 'Great point!', 'Love this!', 'So true!', or similar. "
        "Keep replies under 200 characters. Be conversational like texting a friend. "
        "Just output the reply text, nothing else."
    )

    @field_validator("TWEET_INTERVAL_MINUTES")
    @classmethod
    def tweet_interval_must_be_positive(cls, v: int) -> int:
        if v <= 0:
            return 60
        return v

    class Config:
        env_file = ".env"


settings = Settings()
