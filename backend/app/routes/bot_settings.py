from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional
from app.database import get_db
from app.routes.auth import verify_api_key
from app.models.bot_settings import BotSettings

router = APIRouter()


def _get_or_create(db: Session) -> BotSettings:
    s = db.query(BotSettings).first()
    if not s:
        s = BotSettings(id=1)
        db.add(s)
        db.commit()
        db.refresh(s)
    return s


class SettingsUpdate(BaseModel):
    bot_enabled: Optional[bool] = None
    tweets_per_day: Optional[int] = Field(None, ge=1, le=50)
    tweet_interval_minutes: Optional[int] = Field(None, ge=10, le=1440)
    active_hours_start: Optional[int] = Field(None, ge=0, le=23)
    active_hours_end: Optional[int] = Field(None, ge=0, le=23)
    auto_reply_enabled: Optional[bool] = None
    max_replies_per_cycle: Optional[int] = Field(None, ge=0, le=20)
    max_likes_per_cycle: Optional[int] = Field(None, ge=0, le=20)
    max_retweets_per_cycle: Optional[int] = Field(None, ge=0, le=10)
    min_followers_to_reply: Optional[int] = Field(None, ge=0, le=1000000)
    min_likes_to_retweet: Optional[int] = Field(None, ge=0, le=10000)
    random_skip_chance: Optional[int] = Field(None, ge=0, le=100)
    min_delay_seconds: Optional[int] = Field(None, ge=0, le=60)
    max_delay_seconds: Optional[int] = Field(None, ge=1, le=120)
    auto_refill_enabled: Optional[bool] = None
    refill_threshold: Optional[int] = Field(None, ge=1, le=100)
    refill_count: Optional[int] = Field(None, ge=10, le=500)
    tweet_persona: Optional[str] = None
    reply_persona: Optional[str] = None


class SettingsResponse(BaseModel):
    bot_enabled: bool
    tweets_per_day: int
    tweet_interval_minutes: int
    active_hours_start: int
    active_hours_end: int
    auto_reply_enabled: bool
    max_replies_per_cycle: int
    max_likes_per_cycle: int
    max_retweets_per_cycle: int
    min_followers_to_reply: int
    min_likes_to_retweet: int
    random_skip_chance: int
    min_delay_seconds: int
    max_delay_seconds: int
    auto_refill_enabled: bool
    refill_threshold: int
    refill_count: int
    tweet_persona: str
    reply_persona: str

    class Config:
        from_attributes = True


@router.get("/", response_model=SettingsResponse)
def get_settings(
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    return _get_or_create(db)


@router.patch("/", response_model=SettingsResponse)
def update_settings(
    payload: SettingsUpdate,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    s = _get_or_create(db)
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(s, key, value)
    db.commit()
    db.refresh(s)
    return s


# Backward-compatible persona endpoints (old frontend uses these)
class PersonaResponse(BaseModel):
    bot_persona: str
    reply_persona: str


class PersonaUpdate(BaseModel):
    bot_persona: Optional[str] = None
    reply_persona: Optional[str] = None


@router.get("/persona", response_model=PersonaResponse)
def get_persona(
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    s = _get_or_create(db)
    return PersonaResponse(bot_persona=s.tweet_persona, reply_persona=s.reply_persona)


@router.patch("/persona", response_model=PersonaResponse)
def update_persona(
    payload: PersonaUpdate,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    s = _get_or_create(db)
    if payload.bot_persona is not None:
        s.tweet_persona = payload.bot_persona
    if payload.reply_persona is not None:
        s.reply_persona = payload.reply_persona
    db.commit()
    db.refresh(s)
    return PersonaResponse(bot_persona=s.tweet_persona, reply_persona=s.reply_persona)
