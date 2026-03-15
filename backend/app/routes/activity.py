from fastapi import APIRouter, Depends, Query

from app.database import SessionLocal
from app.models.tweet import InteractionLog, TweetLog
from app.routes.auth import verify_api_key

router = APIRouter()


@router.get("/")
def get_activity(
    limit: int = Query(50, ge=1, le=200),
    api_key: str = Depends(verify_api_key),
):
    db = SessionLocal()
    try:
        # Get recent interactions (likes, retweets, replies, posts)
        interactions = (
            db.query(InteractionLog)
            .order_by(InteractionLog.created_at.desc())
            .limit(limit)
            .all()
        )

        # Get recent tweet logs for content info
        logs = (
            db.query(TweetLog)
            .order_by(TweetLog.sent_at.desc())
            .limit(limit)
            .all()
        )

        # Build activity feed combining both sources
        activity = []

        for log in logs:
            activity.append({
                "type": "posted",
                "content": log.content[:120] if log.content else "",
                "source": log.source,
                "tweet_id": log.tweet_id,
                "timestamp": log.sent_at.isoformat() if log.sent_at else None,
                "metrics": {
                    "likes": log.likes,
                    "retweets": log.retweets,
                    "impressions": log.impressions,
                    "replies": log.replies,
                },
            })

        for interaction in interactions:
            # Skip "posted" interactions since they're already covered by tweet logs
            if interaction.interaction_type.value == "posted":
                continue
            activity.append({
                "type": interaction.interaction_type.value,
                "content": "",
                "source": "bot",
                "tweet_id": interaction.tweet_id,
                "timestamp": interaction.created_at.isoformat() if interaction.created_at else None,
                "metrics": None,
            })

        # Sort by timestamp descending
        activity.sort(key=lambda x: x["timestamp"] or "", reverse=True)

        # Count today's stats
        from datetime import datetime, timezone

        today = datetime.now(timezone.utc).date()
        today_activity = [
            a for a in activity
            if a["timestamp"] and datetime.fromisoformat(a["timestamp"]).date() == today
        ]

        stats = {
            "posts_today": sum(1 for a in today_activity if a["type"] == "posted"),
            "replies_today": sum(1 for a in today_activity if a["type"] == "replied"),
            "likes_today": sum(1 for a in today_activity if a["type"] == "liked"),
            "retweets_today": sum(1 for a in today_activity if a["type"] == "retweeted"),
        }

        return {
            "activity": activity[:limit],
            "stats": stats,
        }
    finally:
        db.close()
