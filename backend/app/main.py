from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

import logging

from app.database import engine, Base, SessionLocal
from app.routes import tweets, scheduler, analytics, queue, auth, settings, activity
from app.services.scheduler_service import scheduler_service

logger = logging.getLogger(__name__)


def _refresh_queue():
    """Clear old pending tweets and generate 100 fresh ones on deploy."""
    import threading

    def _do_refresh():
        from app.models.tweet import TweetQueue, TweetStatus
        from app.services.twitter_service import twitter_service

        db = SessionLocal()
        try:
            # Clear all existing pending tweets
            deleted = db.query(TweetQueue).filter(
                TweetQueue.status == TweetStatus.pending
            ).delete()
            db.commit()
            logger.info(f"Cleared {deleted} old pending tweets from queue")

            # Generate 100 fresh tweets with mixed styles
            topics = twitter_service.fetch_trending_topics()
            generated = 0
            for i in range(100):
                # Refresh trends every 10 for diversity
                if i > 0 and i % 10 == 0:
                    topics = twitter_service.fetch_trending_topics()

                tweet_text = twitter_service.generate_tweet(topics)
                if not tweet_text:
                    continue

                # Skip duplicates
                exists = db.query(TweetQueue).filter(
                    TweetQueue.content == tweet_text
                ).first()
                if exists:
                    continue

                tweet = TweetQueue(content=tweet_text, priority=1)
                db.add(tweet)
                db.commit()
                generated += 1
                if generated % 10 == 0:
                    logger.info(f"Generated {generated}/100 fresh tweets...")

            logger.info(f"Queue refresh complete: generated {generated} fresh tweets")
        except Exception as e:
            db.rollback()
            logger.error(f"Queue refresh failed: {e}")
        finally:
            db.close()

    # Run in background thread so it doesn't block startup/health checks
    thread = threading.Thread(target=_do_refresh, daemon=True)
    thread.start()
    logger.info("Started queue refresh in background thread")


def _log_env_debug():
    """Log all env var names and Twitter/API credential status on startup."""
    import os
    from app.config import settings

    all_vars = sorted(os.environ.keys())
    logger.info(f"=== ALL ENV VARS ({len(all_vars)}) ===")
    for var in all_vars:
        # Show value prefix for known credential vars, just name for others
        if var.startswith("TWITTER_") or var in (
            "API_KEY", "ANTHROPIC_API_KEY", "DATABASE_URL", "SECRET_KEY",
        ):
            val = os.environ[var]
            logger.info(f"  {var} = {val[:12]}... (len={len(val)})")
        else:
            logger.info(f"  {var}")

    logger.info("=== SETTINGS VALUES (after pydantic load) ===")
    logger.info(f"  TWITTER_API_KEY = {'SET' if settings.TWITTER_API_KEY else 'EMPTY'} (len={len(settings.TWITTER_API_KEY)})")
    logger.info(f"  TWITTER_API_SECRET = {'SET' if settings.TWITTER_API_SECRET else 'EMPTY'} (len={len(settings.TWITTER_API_SECRET)})")
    logger.info(f"  TWITTER_ACCESS_TOKEN = {'SET' if settings.TWITTER_ACCESS_TOKEN else 'EMPTY'} (len={len(settings.TWITTER_ACCESS_TOKEN)})")
    logger.info(f"  TWITTER_ACCESS_TOKEN_SECRET = {'SET' if settings.TWITTER_ACCESS_TOKEN_SECRET else 'EMPTY'} (len={len(settings.TWITTER_ACCESS_TOKEN_SECRET)})")
    logger.info(f"  TWITTER_BEARER_TOKEN = {'SET' if settings.TWITTER_BEARER_TOKEN else 'EMPTY'} (len={len(settings.TWITTER_BEARER_TOKEN)})")
    logger.info(f"  ANTHROPIC_API_KEY = {'SET' if settings.ANTHROPIC_API_KEY else 'EMPTY'}")
    logger.info(f"  DATABASE_URL = {settings.DATABASE_URL[:30]}...")
    logger.info(f"  API_KEY = {'SET' if settings.API_KEY else 'EMPTY'}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    _log_env_debug()
    Base.metadata.create_all(bind=engine)
    _refresh_queue()
    try:
        scheduler_service.start()
    except Exception as e:
        logger.error(f"Scheduler failed to start: {e}")
    yield
    scheduler_service.shutdown()


app = FastAPI(
    title="Twitter Bot API",
    description="Backend for Twitter Bot control panel",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(tweets.router, prefix="/api/tweets", tags=["tweets"])
app.include_router(scheduler.router, prefix="/api/scheduler", tags=["scheduler"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(queue.router, prefix="/api/queue", tags=["queue"])
app.include_router(settings.router, prefix="/api/settings", tags=["settings"])
app.include_router(activity.router, prefix="/api/activity", tags=["activity"])


@app.get("/")
def root():
    return {"status": "ok", "service": "Twitter Bot API"}


@app.get("/health")
def health():
    return {"status": "healthy", "version": "1.2.0"}
