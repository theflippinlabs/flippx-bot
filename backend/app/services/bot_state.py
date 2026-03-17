"""Persistent bot state backed by the database."""
import logging
from app.database import SessionLocal
from app.models.tweet import BotState

logger = logging.getLogger(__name__)


def _get_or_create(db) -> BotState:
    state = db.query(BotState).filter(BotState.id == 1).first()
    if not state:
        state = BotState(id=1, bot_enabled=True, auto_reply_enabled=True, tweet_interval_minutes=15)
        db.add(state)
        db.commit()
        db.refresh(state)
    return state


def is_bot_enabled() -> bool:
    db = SessionLocal()
    try:
        return _get_or_create(db).bot_enabled
    finally:
        db.close()


def is_auto_reply_enabled() -> bool:
    db = SessionLocal()
    try:
        return _get_or_create(db).auto_reply_enabled
    finally:
        db.close()


def toggle_bot() -> bool:
    """Toggle bot_enabled, return new value."""
    db = SessionLocal()
    try:
        state = _get_or_create(db)
        state.bot_enabled = not state.bot_enabled
        db.commit()
        logger.info(f"Bot enabled toggled to {state.bot_enabled}")
        return state.bot_enabled
    finally:
        db.close()


def toggle_auto_reply() -> bool:
    """Toggle auto_reply_enabled, return new value."""
    db = SessionLocal()
    try:
        state = _get_or_create(db)
        state.auto_reply_enabled = not state.auto_reply_enabled
        db.commit()
        logger.info(f"Auto-reply enabled toggled to {state.auto_reply_enabled}")
        return state.auto_reply_enabled
    finally:
        db.close()


def set_bot_enabled(enabled: bool):
    db = SessionLocal()
    try:
        state = _get_or_create(db)
        state.bot_enabled = enabled
        db.commit()
    finally:
        db.close()


def set_auto_reply_enabled(enabled: bool):
    db = SessionLocal()
    try:
        state = _get_or_create(db)
        state.auto_reply_enabled = enabled
        db.commit()
    finally:
        db.close()


def get_tweet_interval_minutes() -> int:
    db = SessionLocal()
    try:
        state = _get_or_create(db)
        return state.tweet_interval_minutes or 15
    finally:
        db.close()


def set_tweet_interval_minutes(minutes: int):
    db = SessionLocal()
    try:
        state = _get_or_create(db)
        state.tweet_interval_minutes = minutes
        db.commit()
        logger.info(f"Tweet interval set to {minutes} minutes")
    finally:
        db.close()
