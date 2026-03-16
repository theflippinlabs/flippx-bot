import logging
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import APIKeyHeader
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(api_key: str = Depends(api_key_header)):
    # Skip auth if API_KEY was never configured (still default placeholder)
    if settings.API_KEY in ("your-dashboard-api-key", "your-strong-random-api-key-here", ""):
        return api_key or "no-key"
    received = f"{api_key[:8]}...(len={len(api_key)})" if api_key else "NONE"
    expected = f"{settings.API_KEY[:8]}...(len={len(settings.API_KEY)})"
    if not api_key or api_key != settings.API_KEY:
        logger.warning(f"API key mismatch: received={received}, expected={expected}")
        raise HTTPException(status_code=403, detail="Invalid or missing API key")
    return api_key


@router.get("/me")
def get_profile(api_key: str = Depends(verify_api_key)):
    from app.services.twitter_service import twitter_service
    profile = twitter_service.get_me()
    return profile


@router.get("/status")
def get_bot_status(api_key: str = Depends(verify_api_key)):
    from app.services.scheduler_service import scheduler_service
    from app.services.bot_state import is_bot_enabled, is_auto_reply_enabled
    return {
        "bot_enabled": is_bot_enabled(),
        "auto_reply_enabled": is_auto_reply_enabled(),
        "scheduler_running": scheduler_service.scheduler.running,
        "jobs": scheduler_service.get_jobs(),
    }


@router.post("/toggle")
def toggle_bot(api_key: str = Depends(verify_api_key)):
    from app.services.bot_state import toggle_bot as db_toggle
    new_state = db_toggle()
    return {"bot_enabled": new_state}


@router.post("/run-cycle")
def run_cycle(api_key: str = Depends(verify_api_key)):
    import threading
    from app.services.twitter_service import twitter_service

    thread = threading.Thread(target=twitter_service.run_bot_cycle, daemon=True)
    thread.start()
    return {"triggered": True}


@router.get("/debug-auth")
def debug_auth():
    """Unauthenticated debug endpoint to diagnose API key issues."""
    from fastapi import Request
    return {
        "backend_api_key_len": len(settings.API_KEY) if settings.API_KEY else 0,
        "backend_api_key_full_repr": repr(settings.API_KEY) if settings.API_KEY else "EMPTY",
        "backend_api_key_bytes": [ord(c) for c in settings.API_KEY] if settings.API_KEY else [],
        "is_placeholder": settings.API_KEY in ("your-dashboard-api-key", "your-strong-random-api-key-here", ""),
    }


@router.get("/debug-auth-test")
def debug_auth_test(api_key: str = Depends(api_key_header)):
    """Test what key is received in the header."""
    return {
        "received_key_repr": repr(api_key) if api_key else "NONE",
        "received_key_len": len(api_key) if api_key else 0,
        "received_key_bytes": [ord(c) for c in api_key] if api_key else [],
        "expected_key_repr": repr(settings.API_KEY),
        "expected_key_len": len(settings.API_KEY),
        "match": api_key == settings.API_KEY if api_key else False,
        "stripped_match": api_key.strip() == settings.API_KEY.strip() if api_key else False,
    }


@router.get("/debug-env")
def debug_env(api_key: str = Depends(verify_api_key)):
    """Show all env var names and which Twitter vars pydantic loaded."""
    import os
    all_env_names = sorted(os.environ.keys())
    twitter_vars = {k: f"{os.environ[k][:12]}... (len={len(os.environ[k])})"
                    for k in all_env_names if "TWITTER" in k or "API" in k or "KEY" in k}
    return {
        "total_env_vars": len(all_env_names),
        "all_env_names": all_env_names,
        "twitter_and_api_vars_from_os": twitter_vars,
        "pydantic_settings_loaded": {
            "TWITTER_API_KEY": f"len={len(settings.TWITTER_API_KEY)}, val={settings.TWITTER_API_KEY[:8]}..." if settings.TWITTER_API_KEY else "EMPTY",
            "TWITTER_API_SECRET": f"len={len(settings.TWITTER_API_SECRET)}" if settings.TWITTER_API_SECRET else "EMPTY",
            "TWITTER_ACCESS_TOKEN": f"len={len(settings.TWITTER_ACCESS_TOKEN)}, val={settings.TWITTER_ACCESS_TOKEN[:8]}..." if settings.TWITTER_ACCESS_TOKEN else "EMPTY",
            "TWITTER_ACCESS_TOKEN_SECRET": f"len={len(settings.TWITTER_ACCESS_TOKEN_SECRET)}" if settings.TWITTER_ACCESS_TOKEN_SECRET else "EMPTY",
            "TWITTER_BEARER_TOKEN": f"len={len(settings.TWITTER_BEARER_TOKEN)}" if settings.TWITTER_BEARER_TOKEN else "EMPTY",
            "API_KEY": f"len={len(settings.API_KEY)}" if settings.API_KEY else "EMPTY",
            "DATABASE_URL": f"{settings.DATABASE_URL[:30]}...",
        },
    }


@router.get("/test-twitter")
def test_twitter_auth(api_key: str = Depends(verify_api_key)):
    """Diagnostic endpoint — shows exact Twitter error codes and messages."""
    import tweepy
    from app.services.twitter_service import twitter_service

    results = {
        "credentials_set": {
            "TWITTER_API_KEY": bool(settings.TWITTER_API_KEY),
            "TWITTER_API_SECRET": bool(settings.TWITTER_API_SECRET),
            "TWITTER_ACCESS_TOKEN": bool(settings.TWITTER_ACCESS_TOKEN),
            "TWITTER_ACCESS_TOKEN_SECRET": bool(settings.TWITTER_ACCESS_TOKEN_SECRET),
            "TWITTER_BEARER_TOKEN": bool(settings.TWITTER_BEARER_TOKEN),
        },
        "credential_prefixes": {
            "API_KEY": settings.TWITTER_API_KEY[:8] + "..." if settings.TWITTER_API_KEY else None,
            "ACCESS_TOKEN": settings.TWITTER_ACCESS_TOKEN[:8] + "..." if settings.TWITTER_ACCESS_TOKEN else None,
        },
        "oauth1_test": None,
        "bearer_test": None,
        "checklist": [],
    }

    # Test OAuth 1.0a (user context) — this is what 401s
    try:
        me = twitter_service.client.get_me(user_auth=True)
        results["oauth1_test"] = {
            "success": True,
            "username": me.data.username if me.data else None,
        }
    except tweepy.Unauthorized as e:
        results["oauth1_test"] = {
            "success": False,
            "http_status": 401,
            "error_type": "Unauthorized",
            "raw_error": str(e),
            "api_errors": e.api_errors if hasattr(e, "api_errors") else None,
            "api_codes": e.api_codes if hasattr(e, "api_codes") else None,
            "api_messages": e.api_messages if hasattr(e, "api_messages") else None,
            "response_text": e.response.text if hasattr(e, "response") and e.response else None,
        }
        results["checklist"] = [
            "1. Go to console.x.com > your App > Settings > User authentication settings",
            "2. Ensure App permissions = 'Read and Write' (not just 'Read')",
            "3. After changing permissions: go to Keys and tokens tab",
            "4. REGENERATE both Access Token AND Access Token Secret",
            "5. Update the new tokens in Railway env vars",
            "6. Redeploy the backend",
            "7. Make sure the app is attached to a Project (not standalone)",
        ]
    except tweepy.Forbidden as e:
        results["oauth1_test"] = {
            "success": False,
            "http_status": 403,
            "error_type": "Forbidden",
            "raw_error": str(e),
            "api_errors": e.api_errors if hasattr(e, "api_errors") else None,
            "response_text": e.response.text if hasattr(e, "response") and e.response else None,
        }
    except Exception as e:
        results["oauth1_test"] = {
            "success": False,
            "error_type": type(e).__name__,
            "raw_error": str(e),
        }

    # Test Bearer Token (app context)
    try:
        search = twitter_service.bearer_client.search_recent_tweets(
            query="hello", max_results=10
        )
        results["bearer_test"] = {
            "success": True,
            "tweets_found": len(search.data) if search.data else 0,
        }
    except tweepy.Unauthorized as e:
        results["bearer_test"] = {
            "success": False,
            "http_status": 401,
            "raw_error": str(e),
            "response_text": e.response.text if hasattr(e, "response") and e.response else None,
        }
    except tweepy.Forbidden as e:
        results["bearer_test"] = {
            "success": False,
            "http_status": 403,
            "raw_error": str(e),
            "response_text": e.response.text if hasattr(e, "response") and e.response else None,
        }
    except Exception as e:
        results["bearer_test"] = {
            "success": False,
            "error_type": type(e).__name__,
            "raw_error": str(e),
        }

    return results
