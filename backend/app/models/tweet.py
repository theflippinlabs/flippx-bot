from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Enum
from sqlalchemy.sql import func
from app.database import Base
import enum


class InteractionType(str, enum.Enum):
    liked = "liked"
    retweeted = "retweeted"
    replied = "replied"
    posted = "posted"


class TweetStatus(str, enum.Enum):
    pending = "pending"
    sent = "sent"
    failed = "failed"
    cancelled = "cancelled"


class TweetQueue(Base):
    __tablename__ = "tweet_queue"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    status = Column(Enum(TweetStatus), default=TweetStatus.pending)
    priority = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    sent_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    tweet_id = Column(String, nullable=True)


class ScheduledTweet(Base):
    __tablename__ = "scheduled_tweets"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    scheduled_at = Column(DateTime(timezone=True), nullable=False)
    status = Column(Enum(TweetStatus), default=TweetStatus.pending)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    sent_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    tweet_id = Column(String, nullable=True)
    job_id = Column(String, nullable=True)


class TweetLog(Base):
    __tablename__ = "tweet_logs"

    id = Column(Integer, primary_key=True, index=True)
    tweet_id = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    likes = Column(Integer, default=0)
    retweets = Column(Integer, default=0)
    impressions = Column(Integer, default=0)
    replies = Column(Integer, default=0)
    source = Column(String, default="manual")  # manual, queue, scheduled, bot


class InteractionLog(Base):
    __tablename__ = "interaction_logs"

    id = Column(Integer, primary_key=True, index=True)
    tweet_id = Column(String, nullable=False, unique=True, index=True)
    interaction_type = Column(Enum(InteractionType), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
