from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from datetime import datetime
from app.database import get_db
from app.routes.auth import verify_api_key
from app.models.tweet import ScheduledTweet, TweetStatus
from app.services.scheduler_service import scheduler_service

router = APIRouter()


class ScheduleTweetCreate(BaseModel):
    content: str = Field(..., max_length=280)
    scheduled_at: datetime


@router.post("/")
def create_scheduled_tweet(
    payload: ScheduleTweetCreate,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    if payload.scheduled_at <= datetime.utcnow():
        raise HTTPException(status_code=400, detail="scheduled_at must be in the future")

    tweet = ScheduledTweet(
        content=payload.content,
        scheduled_at=payload.scheduled_at,
    )
    db.add(tweet)
    db.commit()
    db.refresh(tweet)

    job_id = scheduler_service.schedule_tweet(tweet.id, payload.scheduled_at, payload.content)
    tweet.job_id = job_id
    db.commit()
    return tweet


@router.get("/")
def list_scheduled_tweets(
    status: str = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    query = db.query(ScheduledTweet)
    if status:
        query = query.filter(ScheduledTweet.status == status)
    tweets = query.order_by(ScheduledTweet.scheduled_at.asc()).offset(skip).limit(limit).all()
    total = query.count()
    return {"tweets": tweets, "total": total}


@router.delete("/{tweet_id}")
def cancel_scheduled_tweet(
    tweet_id: int,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    tweet = db.query(ScheduledTweet).filter(ScheduledTweet.id == tweet_id).first()
    if not tweet:
        raise HTTPException(status_code=404, detail="Scheduled tweet not found")
    if tweet.status != TweetStatus.pending:
        raise HTTPException(status_code=400, detail="Tweet is not pending")

    if tweet.job_id:
        scheduler_service.cancel_scheduled_tweet(tweet.job_id)

    tweet.status = TweetStatus.cancelled
    db.commit()
    return {"message": "Scheduled tweet cancelled"}
