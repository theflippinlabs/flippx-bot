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
    from sqlalchemy import cast, Date

    cutoff = datetime.utcnow() - timedelta(days=days)
    results = (
        db.query(
            cast(TweetLog.sent_at, Date).label("date"),
            func.count(TweetLog.id).label("tweets"),
            func.sum(TweetLog.likes).label("likes"),
            func.sum(TweetLog.retweets).label("retweets"),
            func.sum(TweetLog.impressions).label("impressions"),
        )
        .filter(TweetLog.sent_at >= cutoff)
        .group_by(cast(TweetLog.sent_at, Date))
        .order_by(cast(TweetLog.sent_at, Date))
        .all()
    )
    return [
        {
            "date": str(r.date),
            "tweets": r.tweets,
            "likes": r.likes or 0,
            "retweets": r.retweets or 0,
            "impressions": r.impressions or 0,
        }
        for r in results
    ]
