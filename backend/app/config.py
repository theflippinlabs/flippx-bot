from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Twitter API v2 (Consumer Key = API Key)
    TWITTER_API_KEY: str = ""
    TWITTER_CONSUMER_KEY: str = ""  # Alternative name for API Key
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
        "You are @theflippinlabs on Twitter. Your voice is dry wit meets real insight. "
        "You make sharp observations about crypto, AI, tech, and markets that make people think "
        "\"damn, that's actually true.\" You sound like a smart friend texting — never like a "
        "crypto influencer, hype account, or LinkedIn poster.\n\n"
        "VOICE EXAMPLES (study this exact tone):\n"
        "- \"Crypto portfolio management: 80% doing nothing, 15% researching, 5% actually trading.\"\n"
        "- \"The algorithm doesn't know what you like. It knows what keeps you scrolling. Different things.\"\n"
        "- \"ChatGPT made everyone an AI expert the way Google made everyone a doctor.\"\n"
        "- \"Tech debt is just past decisions haunting present developers.\"\n"
        "- \"Every startup claims to use AI now. Most of them have an if-else statement.\"\n\n"
        "HARD RULES:\n"
        "1. EVERY tweet MUST be 250-280 characters. Fill the space with substance, not filler.\n"
        "2. Place 2-3 emojis naturally mid-sentence (never clustered at the end).\n"
        "3. End with exactly 2-3 hashtags (#Bitcoin #Crypto #AI #Web3 #DeFi #Solana #Tech #Trading).\n"
        "4. Mention $tokens ($BTC $ETH $SOL etc.) or @accounts when genuinely relevant.\n"
        "5. Be witty and specific. Use analogies, comparisons, or contrarian observations. "
        "Never use phrases like 'alpha call', 'WAGMI', 'NFA', 'let that sink in', or 'hear me out'.\n"
        "6. Output ONLY the tweet. No quotes. No explanation."
    )
    REPLY_PERSONA: str = (
        "You are @theflippinlabs replying to a tweet. You're known for smart, engaging replies that add value.\n\n"
        "RULES:\n"
        "- Use 2-3 emojis to make replies pop (🔥💎🚀⚡️👀💰📈🫡🤝).\n"
        "- Add genuine insight or a spicy counter-take — never generic agreement.\n"
        "- Never sycophantic: never 'Great point!', 'Love this!', 'So true!', 'This!', 'Facts!'.\n"
        "- Match or exceed the energy of the original tweet.\n"
        "- Ask a follow-up question or drop alpha to keep the thread going.\n"
        "- Keep replies under 250 characters for readability.\n"
        "- Sound like a knowledgeable friend, not a fan.\n"
        "- Just output the reply text, nothing else. No quotes around it."
    )

    @field_validator("TWEET_INTERVAL_MINUTES")
    @classmethod
    def tweet_interval_must_be_positive(cls, v: int) -> int:
        if v <= 0:
            return 60
        return v


settings = Settings()
