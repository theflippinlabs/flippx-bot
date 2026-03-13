from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.sql import func
from app.database import Base


class AutoReplyRule(Base):
    __tablename__ = "auto_reply_rules"

    id = Column(Integer, primary_key=True, index=True)
    keyword = Column(String, nullable=False)
    reply_template = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    match_type = Column(String, default="contains")  # contains, exact, regex
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    trigger_count = Column(Integer, default=0)
    last_triggered = Column(DateTime(timezone=True), nullable=True)
