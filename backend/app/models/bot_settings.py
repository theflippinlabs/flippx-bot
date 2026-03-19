from sqlalchemy import Column, Integer, String, Boolean, Text
from app.database import Base


class BotSettings(Base):
    __tablename__ = "bot_settings"

    id = Column(Integer, primary_key=True, default=1)
    # Posting
    bot_enabled = Column(Boolean, default=True)
    tweets_per_day = Column(Integer, default=6)  # max tweets posted per day
    tweet_interval_minutes = Column(Integer, default=30)  # min gap between posts
    active_hours_start = Column(Integer, default=7)  # 7 AM
    active_hours_end = Column(Integer, default=23)  # 11 PM
    # Engagement
    auto_reply_enabled = Column(Boolean, default=True)
    max_replies_per_cycle = Column(Integer, default=3)
    max_likes_per_cycle = Column(Integer, default=5)
    max_retweets_per_cycle = Column(Integer, default=0)
    min_followers_to_reply = Column(Integer, default=1000)
    min_followers_to_retweet = Column(Integer, default=10000)
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
    tweet_persona = Column(Text, default="Confident, sharp, slightly provocative but always credible. Natural conversational English like a real Twitter power user. Mix of short punchy takes, bold statements, questions to the audience. 1-3 emojis max per tweet, sometimes none. Never use markdown, dashes, or special characters.")
    reply_persona = Column(Text, default="Engaging, smart, adds value to the conversation. Short and punchy. Never sycophantic. Feels like a real human reply, not a bot.")
