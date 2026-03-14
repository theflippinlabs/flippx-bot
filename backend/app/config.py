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

    @field_validator("TWEET_INTERVAL_MINUTES")
    @classmethod
    def tweet_interval_must_be_positive(cls, v: int) -> int:
        if v <= 0:
            return 60
        return v

    class Config:
        env_file = ".env"


settings = Settings()
