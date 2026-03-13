from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from app.database import get_db
from app.routes.auth import verify_api_key
from app.services.twitter_service import twitter_service
from app.models.tweet import TweetLog

router = APIRouter()


class TweetCreate(BaseModel):
    content: str = Field(..., max_length=280)


@router.post("/send")
def send_tweet(payload: TweetCreate, db: Session = Depends(get_db), api_key: str = Depends(verify_api_key)):
    result = twitter_service.post_tweet(payload.content)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error"))

    log = TweetLog(
        tweet_id=result["tweet_id"],
        content=payload.content,
        source="manual",
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return {"tweet_id": result["tweet_id"], "log_id": log.id}


@router.get("/logs")
def get_tweet_logs(skip: int = 0, limit: int = 50, db: Session = Depends(get_db), api_key: str = Depends(verify_api_key)):
    logs = db.query(TweetLog).order_by(TweetLog.sent_at.desc()).offset(skip).limit(limit).all()
    total = db.query(TweetLog).count()
    return {"logs": logs, "total": total}
