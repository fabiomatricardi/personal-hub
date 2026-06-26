import json
import os
import sys
import httpx
from datetime import datetime

if getattr(sys, "frozen", False):
    DATA_DIR = os.path.join(os.path.dirname(sys.executable), "data")
else:
    DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")

DB_FILE = os.path.join(DATA_DIR, "telegram_files_db.json")


def _ensure_dirs():
    os.makedirs(DATA_DIR, exist_ok=True)


def load_db() -> dict:
    _ensure_dirs()
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                db = json.load(f)
            db.setdefault("last_update_id", 0)
            db.setdefault("saved_files", [])
            db.setdefault("total_saved", 0)
            db.setdefault("history", [])
            return db
        except (json.JSONDecodeError, IOError):
            pass
    return {
        "last_update_id": 0,
        "saved_files": [],
        "total_saved": 0,
        "history": [],
    }


def save_db(db: dict):
    _ensure_dirs()
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2, ensure_ascii=False)


def fetch_file_messages(token: str, last_update_id: int) -> tuple[list[dict], int]:
    try:
        with httpx.Client(timeout=30) as client:
            resp = client.get(
                f"https://api.telegram.org/bot{token}/getUpdates",
                params={"offset": last_update_id + 1, "timeout": 5},
            )
            resp.raise_for_status()
            data = resp.json()
    except Exception:
        return [], last_update_id

    if not data.get("ok"):
        return [], last_update_id

    updates = data.get("result", [])
    new_last_id = last_update_id
    file_messages = []

    for update in updates:
        update_id = update.get("update_id", 0)
        if update_id > new_last_id:
            new_last_id = update_id

        msg = update.get("message")
        if not msg:
            continue

        doc = msg.get("document")
        photos = msg.get("photo")

        if doc:
            file_id = doc.get("file_id", "")
            file_name = doc.get("file_name", f"doc_{msg.get('message_id', 0)}")
            file_size = doc.get("file_size", 0)
            file_messages.append({
                "message_id": msg.get("message_id", 0),
                "file_id": file_id,
                "file_name": file_name,
                "file_size": file_size,
                "date": msg.get("date", 0),
            })
        elif photos:
            largest = max(photos, key=lambda p: p.get("file_size", 0))
            file_id = largest.get("file_id", "")
            file_size = largest.get("file_size", 0)
            file_name = f"photo_{msg.get('message_id', 0)}.jpg"
            file_messages.append({
                "message_id": msg.get("message_id", 0),
                "file_id": file_id,
                "file_name": file_name,
                "file_size": file_size,
                "date": msg.get("date", 0),
            })

    return file_messages, new_last_id


def download_file(token: str, file_id: str, save_dir: str, file_name: str) -> dict:
    try:
        with httpx.Client(timeout=60) as client:
            info_resp = client.get(
                f"https://api.telegram.org/bot{token}/getFile",
                params={"file_id": file_id},
            )
            info_resp.raise_for_status()
            info_data = info_resp.json()

            if not info_data.get("ok"):
                return {"ok": False, "error": f"getFile failed: {info_data}"}

            file_path = info_data["result"].get("file_path", "")
            if not file_path:
                return {"ok": False, "error": "No file_path in getFile response"}

            dl_resp = client.get(
                f"https://api.telegram.org/file/bot{token}/{file_path}",
            )
            dl_resp.raise_for_status()

            full_path = os.path.join(save_dir, file_name)
            with open(full_path, "wb") as f:
                f.write(dl_resp.content)

            return {"ok": True, "path": full_path}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def run_files_job(config: dict) -> dict:
    from backend.services.config import load_config

    if not config:
        config = load_config()

    result = {
        "timestamp": datetime.now().isoformat(),
        "files_found": 0,
        "files_saved": 0,
        "duplicates_skipped": 0,
        "errors": [],
    }

    token = config.get("telegram_bot_token", "")
    if not token:
        result["errors"].append("No Telegram bot token configured")
        return result

    files_dir = config.get("telegram_files_dir", "./telegram_files/")
    if not os.path.isabs(files_dir):
        project_root = os.path.join(os.path.dirname(__file__), "..", "..")
        files_dir = os.path.normpath(os.path.join(project_root, files_dir))

    os.makedirs(files_dir, exist_ok=True)

    db = load_db()
    last_id = db.get("last_update_id", 0)

    file_messages, new_last_id = fetch_file_messages(token, last_id)
    result["files_found"] = len(file_messages)

    saved_names = {sf["file_name"] for sf in db.get("saved_files", [])}

    for fm in file_messages:
        fname = fm["file_name"]

        if fname in saved_names:
            result["duplicates_skipped"] += 1
            continue

        dl_result = download_file(token, fm["file_id"], files_dir, fname)
        if dl_result.get("ok"):
            saved_names.add(fname)
            db.setdefault("saved_files", []).append({
                "file_name": fname,
                "file_id": fm["file_id"],
                "saved_at": datetime.now().isoformat(),
                "message_id": fm["message_id"],
            })
            result["files_saved"] += 1
        else:
            result["errors"].append(f"Download failed for {fname}: {dl_result.get('error', 'unknown')}")

    db["last_update_id"] = new_last_id
    db["total_saved"] = len(db.get("saved_files", []))

    db.setdefault("history", []).append({
        "timestamp": result["timestamp"],
        "files_found": result["files_found"],
        "files_saved": result["files_saved"],
        "duplicates_skipped": result["duplicates_skipped"],
        "errors": result["errors"],
    })
    if len(db["history"]) > 100:
        db["history"] = db["history"][-100:]

    save_db(db)
    return result
