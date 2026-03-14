from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import APIKeyHeader
from app.config import settings

router = APIRouter()
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(api_key: str = Depends(api_key_header)):
    if api_key != settings.API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return api_key


@router.get("/me")
def get_profile(api_key: str = Depends(verify_api_key)):
    from app.services.twitter_service import twitter_service
    profile = twitter_service.get_me()
    return profile


@router.get("/status")
def get_bot_status(api_key: str = Depends(verify_api_key)):
    from app.services.scheduler_service import scheduler_service
    return {
        "bot_enabled": settings.BOT_ENABLED,
        "auto_reply_enabled": settings.AUTO_REPLY_ENABLED,
        "scheduler_running": scheduler_service.scheduler.running,
        "jobs": scheduler_service.get_jobs(),
    }
