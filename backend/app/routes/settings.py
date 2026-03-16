from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.config import settings
from app.routes.auth import verify_api_key
from app.services import bot_state

router = APIRouter()


class SettingsUpdate(BaseModel):
    tweet_interval_minutes: int | None = None
    replies_per_run: int | None = None
    likes_per_run: int | None = None
    retweets_per_run: int | None = None


class PersonaUpdate(BaseModel):
    bot_persona: str | None = None
    reply_persona: str | None = None


@router.get("/")
def get_settings(api_key: str = Depends(verify_api_key)):
    return {
        "tweet_interval_minutes": settings.TWEET_INTERVAL_MINUTES,
        "replies_per_run": settings.REPLIES_PER_RUN,
        "likes_per_run": settings.LIKES_PER_RUN,
        "retweets_per_run": settings.RETWEETS_PER_RUN,
        "bot_enabled": bot_state.is_bot_enabled(),
        "auto_reply_enabled": bot_state.is_auto_reply_enabled(),
    }


@router.patch("/")
def update_settings(data: SettingsUpdate, api_key: str = Depends(verify_api_key)):
    if data.tweet_interval_minutes is not None and data.tweet_interval_minutes > 0:
        settings.TWEET_INTERVAL_MINUTES = data.tweet_interval_minutes
    if data.replies_per_run is not None and data.replies_per_run >= 0:
        settings.REPLIES_PER_RUN = data.replies_per_run
    if data.likes_per_run is not None and data.likes_per_run >= 0:
        settings.LIKES_PER_RUN = data.likes_per_run
    if data.retweets_per_run is not None and data.retweets_per_run >= 0:
        settings.RETWEETS_PER_RUN = data.retweets_per_run
    return {"status": "updated"}


@router.get("/persona")
def get_persona(api_key: str = Depends(verify_api_key)):
    return {
        "bot_persona": settings.BOT_PERSONA,
        "reply_persona": settings.REPLY_PERSONA,
    }


@router.patch("/persona")
def update_persona(data: PersonaUpdate, api_key: str = Depends(verify_api_key)):
    if data.bot_persona is not None:
        settings.BOT_PERSONA = data.bot_persona
    if data.reply_persona is not None:
        settings.REPLY_PERSONA = data.reply_persona
    return {"status": "updated"}
