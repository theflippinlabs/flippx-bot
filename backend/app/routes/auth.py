from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import APIKeyHeader
from app.config import settings

router = APIRouter()
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(api_key: str = Depends(api_key_header)):
    if api_key != settings.API_KEY.strip():
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
    from app.database import SessionLocal
    from app.models.bot_settings import BotSettings

    db = SessionLocal()
    try:
        s = db.query(BotSettings).first()
        bot_enabled = s.bot_enabled if s else settings.BOT_ENABLED
        auto_reply = s.auto_reply_enabled if s else settings.AUTO_REPLY_ENABLED
    finally:
        db.close()

    return {
        "bot_enabled": bot_enabled,
        "auto_reply_enabled": auto_reply,
        "scheduler_running": scheduler_service.scheduler.running,
        "jobs": scheduler_service.get_jobs(),
    }


@router.post("/toggle")
def toggle_bot(api_key: str = Depends(verify_api_key)):
    from app.database import SessionLocal
    from app.models.bot_settings import BotSettings

    db = SessionLocal()
    try:
        s = db.query(BotSettings).first()
        if not s:
            s = BotSettings(id=1)
            db.add(s)
        s.bot_enabled = not s.bot_enabled
        db.commit()
        return {"bot_enabled": s.bot_enabled}
    finally:
        db.close()


@router.post("/run-cycle")
def run_bot_cycle(api_key: str = Depends(verify_api_key)):
    from app.services.twitter_service import twitter_service
    try:
        twitter_service.run_bot_cycle()
        return {"message": "Bot cycle triggered"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
