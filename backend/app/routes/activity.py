from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.routes.auth import verify_api_key
from app.models.tweet import TweetLog

router = APIRouter()


@router.get("/")
def get_activity(
    limit: int = 50,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    logs = (
        db.query(TweetLog)
        .order_by(TweetLog.sent_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": log.id,
            "tweet_id": log.tweet_id,
            "content": log.content,
            "source": log.source,
            "sent_at": log.sent_at.isoformat() if log.sent_at else None,
            "likes": log.likes,
            "retweets": log.retweets,
            "impressions": log.impressions,
            "replies": log.replies,
        }
        for log in logs
    ]
