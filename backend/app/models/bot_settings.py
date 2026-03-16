from sqlalchemy import Column, Integer, String, Boolean, Text
from app.database import Base


class BotSettings(Base):
    __tablename__ = "bot_settings"

    id = Column(Integer, primary_key=True, default=1)
    # Posting
    bot_enabled = Column(Boolean, default=True)
    tweets_per_day = Column(Integer, default=6)  # max tweets posted per day
    tweet_interval_minutes = Column(Integer, default=120)  # min gap between posts
    active_hours_start = Column(Integer, default=7)  # 7 AM
    active_hours_end = Column(Integer, default=23)  # 11 PM
    # Engagement
    auto_reply_enabled = Column(Boolean, default=True)
    max_replies_per_cycle = Column(Integer, default=3)
    max_likes_per_cycle = Column(Integer, default=5)
    max_retweets_per_cycle = Column(Integer, default=1)
    min_followers_to_reply = Column(Integer, default=1000)
    min_likes_to_retweet = Column(Integer, default=50)
    # Human-like behavior
    random_skip_chance = Column(Integer, default=15)  # percentage
    min_delay_seconds = Column(Integer, default=2)
    max_delay_seconds = Column(Integer, default=8)
    # Queue
    auto_refill_enabled = Column(Boolean, default=True)
    refill_threshold = Column(Integer, default=20)
    refill_count = Column(Integer, default=100)
    # Persona
    tweet_persona = Column(Text, default="Sharp, witty, conversational. Mix humor with insight. Use 2-3 relevant hashtags. Sound like a smart friend. Max 1-2 emojis. Every tweet under 280 chars.")
    reply_persona = Column(Text, default="Be genuinely engaging, add value, match the energy. Never sycophantic. Keep replies under 200 characters. Be conversational like texting a friend.")
