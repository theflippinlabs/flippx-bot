import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from app.database import get_db
from app.routes.auth import verify_api_key
from app.models.tweet import TweetQueue, TweetStatus
from app.models.auto_reply import AutoReplyRule

logger = logging.getLogger(__name__)
router = APIRouter()


class QueueTweetCreate(BaseModel):
    content: str = Field(..., max_length=280)
    priority: int = Field(default=0, ge=0, le=10)


class AutoReplyCreate(BaseModel):
    keyword: str
    reply_template: str = Field(..., max_length=280)
    match_type: str = Field(default="contains", pattern="^(contains|exact|regex)$")


@router.post("/tweets")
def add_to_queue(
    payload: QueueTweetCreate,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    tweet = TweetQueue(content=payload.content, priority=payload.priority)
    db.add(tweet)
    db.commit()
    db.refresh(tweet)
    return tweet


@router.get("/tweets")
def list_queue(
    status: str = "pending",
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    query = db.query(TweetQueue)
    if status:
        query = query.filter(TweetQueue.status == status)
    tweets = query.order_by(TweetQueue.priority.desc(), TweetQueue.created_at).offset(skip).limit(limit).all()
    total = query.count()
    return {"tweets": tweets, "total": total}


@router.delete("/tweets/{tweet_id}")
def remove_from_queue(
    tweet_id: int,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    tweet = db.query(TweetQueue).filter(TweetQueue.id == tweet_id).first()
    if not tweet:
        raise HTTPException(status_code=404, detail="Tweet not found in queue")
    if tweet.status != TweetStatus.pending:
        raise HTTPException(status_code=400, detail="Can only cancel pending tweets")
    tweet.status = TweetStatus.cancelled
    db.commit()
    return {"message": "Tweet removed from queue"}


@router.post("/generate")
def generate_ai_tweets(
    count: int = 10,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    """Generate AI tweets by scanning Twitter trends and queue them."""
    from app.services.twitter_service import twitter_service

    if count < 1 or count > 50:
        raise HTTPException(status_code=400, detail="Count must be between 1 and 50")

    generated = []
    for i in range(count):
        topics = twitter_service.fetch_trending_topics()
        tweet_text = twitter_service.generate_tweet(topics)
        if not tweet_text:
            logger.warning(f"Failed to generate tweet {i+1}/{count}")
            continue

        # Skip duplicates
        exists = db.query(TweetQueue).filter(TweetQueue.content == tweet_text).first()
        if exists:
            continue

        tweet = TweetQueue(content=tweet_text, priority=1)
        db.add(tweet)
        db.commit()
        db.refresh(tweet)
        generated.append({"id": tweet.id, "content": tweet.content})
        logger.info(f"Generated and queued tweet {i+1}/{count}")

    return {"generated": len(generated), "requested": count, "tweets": generated}


@router.post("/seed")
def seed_queue(
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    """Seed the queue with pre-written crypto/tech tweets from the library."""
    import random
    from seed_tweets import TWEETS

    existing = db.query(TweetQueue).filter(TweetQueue.status == "pending").count()
    added = 0
    for content in TWEETS:
        exists = db.query(TweetQueue).filter(TweetQueue.content == content).first()
        if exists:
            continue
        tweet = TweetQueue(content=content, priority=random.randint(0, 5))
        db.add(tweet)
        added += 1
    db.commit()
    return {"added": added, "previously_pending": existing, "total_in_library": len(TWEETS)}


# Auto-reply rules
@router.get("/rules")
def list_rules(db: Session = Depends(get_db), api_key: str = Depends(verify_api_key)):
    return db.query(AutoReplyRule).all()


@router.post("/rules")
def create_rule(
    payload: AutoReplyCreate,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    rule = AutoReplyRule(**payload.model_dump())
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@router.patch("/rules/{rule_id}/toggle")
def toggle_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    rule = db.query(AutoReplyRule).filter(AutoReplyRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    rule.is_active = not rule.is_active
    db.commit()
    return {"id": rule.id, "is_active": rule.is_active}


@router.delete("/rules/{rule_id}")
def delete_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    rule = db.query(AutoReplyRule).filter(AutoReplyRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    db.delete(rule)
    db.commit()
    return {"message": "Rule deleted"}
