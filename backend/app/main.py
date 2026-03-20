import os

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
    import logging
    from app.config import settings
    _logger = logging.getLogger(__name__)
    if settings.API_KEY in ("your-dashboard-api-key", ""):
        _logger.warning(
            "API_KEY is set to the default value. Set a strong API_KEY env var before deploying."
        )
    if settings.SECRET_KEY == "change-me-in-production":
        _logger.warning(
            "SECRET_KEY is set to the default value. Set a strong SECRET_KEY env var before deploying."
        )
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

_cors_origins = [
    o.strip()
    for o in os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")
    if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
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
