from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.routes.auth import verify_api_key
from app.models.tweet import TweetLog, TweetQueue, ScheduledTweet, TweetStatus

router = APIRouter()


@router.get("/overview")
def get_overview(db: Session = Depends(get_db), api_key: str = Depends(verify_api_key)):
    total_tweets = db.query(TweetLog).count()
    total_likes = db.query(func.sum(TweetLog.likes)).scalar() or 0
    total_retweets = db.query(func.sum(TweetLog.retweets)).scalar() or 0
    total_impressions = db.query(func.sum(TweetLog.impressions)).scalar() or 0
    queue_pending = db.query(TweetQueue).filter(TweetQueue.status == TweetStatus.pending).count()
    scheduled_pending = db.query(ScheduledTweet).filter(ScheduledTweet.status == TweetStatus.pending).count()

    return {
        "total_tweets": total_tweets,
        "total_likes": total_likes,
        "total_retweets": total_retweets,
        "total_impressions": total_impressions,
        "engagement_rate": round((total_likes + total_retweets) / max(total_impressions, 1) * 100, 2),
        "queue_pending": queue_pending,
        "scheduled_pending": scheduled_pending,
    }


@router.get("/top-tweets")
def get_top_tweets(
    metric: str = "likes",
    limit: int = 10,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    order_col = getattr(TweetLog, metric, TweetLog.likes)
    tweets = db.query(TweetLog).order_by(order_col.desc()).limit(limit).all()
    return tweets


@router.get("/timeline")
def get_timeline(
    days: int = 7,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    from datetime import datetime, timedelta

    cutoff = datetime.utcnow() - timedelta(days=days)
    logs = (
        db.query(TweetLog)
        .filter(TweetLog.sent_at >= cutoff)
        .order_by(TweetLog.sent_at)
        .all()
    )

    # Group by date in Python to avoid PostgreSQL cast issues
    by_date: dict = {}
    for log in logs:
        if log.sent_at:
            d = log.sent_at.strftime("%Y-%m-%d")
            if d not in by_date:
                by_date[d] = {"date": d, "tweets": 0, "likes": 0, "retweets": 0, "impressions": 0}
            by_date[d]["tweets"] += 1
            by_date[d]["likes"] += log.likes or 0
            by_date[d]["retweets"] += log.retweets or 0
            by_date[d]["impressions"] += log.impressions or 0

    return sorted(by_date.values(), key=lambda x: x["date"])
