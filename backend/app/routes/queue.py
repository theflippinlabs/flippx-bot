from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from app.database import get_db
from app.routes.auth import verify_api_key
from app.models.tweet import TweetQueue, TweetStatus
from app.models.auto_reply import AutoReplyRule

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
