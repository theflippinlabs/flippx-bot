from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

import logging

from app.database import engine, Base, SessionLocal
from app.routes import tweets, scheduler, analytics, queue, auth, settings, activity
from app.services.scheduler_service import scheduler_service

logger = logging.getLogger(__name__)


def _auto_seed_queue():
    """Seed the tweet queue on first deploy if empty."""
    import random
    from app.models.tweet import TweetQueue
    try:
        from seed_tweets import TWEETS
    except ImportError:
        logger.warning("seed_tweets module not found, skipping auto-seed")
        return

    db = SessionLocal()
    try:
        pending = db.query(TweetQueue).filter(TweetQueue.status == "pending").count()
        if pending > 0:
            logger.info(f"Queue already has {pending} pending tweets, skipping seed")
            return

        added = 0
        for content in TWEETS:
            tweet = TweetQueue(content=content, priority=random.randint(0, 5))
            db.add(tweet)
            added += 1
        db.commit()
        logger.info(f"Auto-seeded {added} tweets into queue")
    except Exception as e:
        db.rollback()
        logger.error(f"Auto-seed failed: {e}")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    _auto_seed_queue()
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
    return {"status": "healthy"}
