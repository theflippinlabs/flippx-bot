from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import APIKeyHeader
from app.config import settings

router = APIRouter()
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(api_key: str = Depends(api_key_header)):
    if api_key != settings.API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return api_key


@router.get("/me")
def get_profile(api_key: str = Depends(verify_api_key)):
    from app.services.twitter_service import twitter_service
    profile = twitter_service.get_me()
    return profile


@router.get("/status")
def get_bot_status(api_key: str = Depends(verify_api_key)):
    from app.services.scheduler_service import scheduler_service
    return {
        "bot_enabled": settings.BOT_ENABLED,
        "auto_reply_enabled": settings.AUTO_REPLY_ENABLED,
        "scheduler_running": scheduler_service.scheduler.running,
        "jobs": scheduler_service.get_jobs(),
    }


@router.post("/toggle")
def toggle_bot(api_key: str = Depends(verify_api_key)):
    settings.BOT_ENABLED = not settings.BOT_ENABLED
    return {"bot_enabled": settings.BOT_ENABLED}


@router.post("/run-cycle")
def run_cycle(api_key: str = Depends(verify_api_key)):
    import threading
    from app.services.twitter_service import twitter_service

    thread = threading.Thread(target=twitter_service.run_bot_cycle, daemon=True)
    thread.start()
    return {"triggered": True}


@router.get("/test-twitter")
def test_twitter_auth(api_key: str = Depends(verify_api_key)):
    """Diagnostic endpoint to test Twitter API credentials."""
    from app.services.twitter_service import twitter_service
    results = {
        "credentials_set": {
            "TWITTER_API_KEY": bool(settings.TWITTER_API_KEY),
            "TWITTER_API_SECRET": bool(settings.TWITTER_API_SECRET),
            "TWITTER_ACCESS_TOKEN": bool(settings.TWITTER_ACCESS_TOKEN),
            "TWITTER_ACCESS_TOKEN_SECRET": bool(settings.TWITTER_ACCESS_TOKEN_SECRET),
            "TWITTER_BEARER_TOKEN": bool(settings.TWITTER_BEARER_TOKEN),
        },
        "oauth1_test": None,
        "bearer_test": None,
    }

    # Test OAuth 1.0a (user context)
    try:
        me = twitter_service.client.get_me(user_auth=True)
        results["oauth1_test"] = {
            "success": True,
            "username": me.data.username if me.data else None,
        }
    except Exception as e:
        results["oauth1_test"] = {"success": False, "error": str(e)}

    # Test Bearer Token (app context)
    try:
        search = twitter_service.bearer_client.search_recent_tweets(
            query="hello", max_results=10
        )
        results["bearer_test"] = {
            "success": True,
            "tweets_found": len(search.data) if search.data else 0,
        }
    except Exception as e:
        results["bearer_test"] = {"success": False, "error": str(e)}

    return results
