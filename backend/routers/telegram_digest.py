from fastapi import APIRouter, HTTPException
from backend.services.config import load_config
from backend.services.telegram_digest import load_db, run_digest_job

router = APIRouter(prefix="/api/telegram-digest", tags=["telegram-digest"])


@router.get("/status")
async def api_status():
    db = load_db()
    return {
        "running": False,
        "last_run": db["history"][-1]["timestamp"] if db.get("history") else None,
        "messages_processed": db.get("total_processed", 0),
        "emails_sent": db.get("total_emails", 0),
    }


@router.post("/run-now")
async def api_run_now():
    try:
        config = load_config()
        result = run_digest_job(config)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Digest job failed: {e}")


@router.get("/history")
async def api_history():
    db = load_db()
    return db.get("history", [])[-50:]
