from fastapi import APIRouter
from backend.services.config import load_config
from backend.services.telegram_files import load_db, run_files_job

router = APIRouter(prefix="/api/telegram-files", tags=["telegram-files"])


@router.get("/status")
async def api_status():
    try:
        db = load_db()
        return {
            "running": False,
            "last_run": db.get("history", [{}])[-1].get("timestamp") if db.get("history") else None,
            "files_saved": db.get("total_saved", 0),
        }
    except Exception:
        return {"running": False, "last_run": None, "files_saved": 0}


@router.post("/run-now")
async def api_run_now():
    try:
        config = load_config()
        return run_files_job(config)
    except Exception as e:
        return {"error": str(e)}


@router.get("/history")
async def api_history():
    try:
        db = load_db()
        return db.get("history", [])[-50:]
    except Exception:
        return []


@router.get("/list")
async def api_list_files():
    try:
        db = load_db()
        return db.get("saved_files", [])
    except Exception:
        return []
