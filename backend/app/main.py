from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.database import engine, Base
from app.routes import tweets, scheduler, analytics, queue, auth, bot_settings, activity
from app.services.scheduler_service import scheduler_service


def _run_migrations():
    """Add any missing columns to existing tables."""
    from sqlalchemy import text, inspect
    with engine.connect() as conn:
        inspector = inspect(engine)
        if "bot_settings" in inspector.get_table_names():
            columns = [c["name"] for c in inspector.get_columns("bot_settings")]
            if "min_followers_to_retweet" not in columns:
                conn.execute(text(
                    "ALTER TABLE bot_settings ADD COLUMN min_followers_to_retweet INTEGER DEFAULT 10000"
                ))
                conn.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    _run_migrations()
    scheduler_service.start()
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
app.include_router(bot_settings.router, prefix="/api/settings", tags=["settings"])
app.include_router(activity.router, prefix="/api/activity", tags=["activity"])


@app.get("/")
def root():
    return {"status": "ok", "service": "Twitter Bot API"}


@app.get("/health")
def health():
    from app.config import settings
    db_type = "postgresql" if "postgresql" in settings.DATABASE_URL else "sqlite"
    return {"status": "healthy", "database": db_type}
