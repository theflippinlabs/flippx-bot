from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func
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
    limit = max(1, min(limit, 500))
    logs = (
        db.query(TweetLog)
        .order_by(TweetLog.sent_at.desc())
        .limit(limit)
        .all()
    )

    # Compute stats for the dashboard
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    total_tweets = db.query(func.count(TweetLog.id)).scalar() or 0
    tweets_today = (
        db.query(func.count(TweetLog.id))
        .filter(TweetLog.sent_at >= today_start)
        .scalar()
        or 0
    )
    total_likes = db.query(func.coalesce(func.sum(TweetLog.likes), 0)).scalar()
    total_retweets = db.query(func.coalesce(func.sum(TweetLog.retweets), 0)).scalar()
    total_impressions = db.query(func.coalesce(func.sum(TweetLog.impressions), 0)).scalar()
    total_replies = db.query(func.coalesce(func.sum(TweetLog.replies), 0)).scalar()

    activity = [
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

    return {
        "stats": {
            "total_tweets": total_tweets,
            "tweets_today": tweets_today,
            "total_likes": total_likes,
            "total_retweets": total_retweets,
            "total_impressions": total_impressions,
            "total_replies": total_replies,
        },
        "activity": activity,
    }
