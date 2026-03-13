from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.database import engine, Base
from app.routes import tweets, scheduler, analytics, queue, auth
from app.services.scheduler_service import scheduler_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
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


@app.get("/")
def root():
    return {"status": "ok", "service": "Twitter Bot API"}


@app.get("/health")
def health():
    return {"status": "healthy"}
