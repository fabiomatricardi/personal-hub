import os
from fastapi import APIRouter
from backend.services.config import load_config
from backend.models import DashboardAppStatus

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

APPS = [
    {"name": "Link Card", "icon": "pi-link", "description": "Generate HTML link cards from URLs"},
    {"name": "Tweet Gen", "icon": "pi-twitter", "description": "Convert articles to tweet threads via LLM"},
    {"name": "Wiki", "icon": "pi-book", "description": "Personal command reference browser"},
    {"name": "TG Digest", "icon": "pi-envelope", "description": "Telegram message digest with AI summaries"},
    {"name": "TG Files", "icon": "pi-download", "description": "Save Telegram file attachments locally"},
    {"name": "Cron Jobs", "icon": "pi-calendar", "description": "Manage scheduled tasks for Telegram apps"},
]


@router.get("")
async def api_dashboard():
    config = load_config()
    wiki_dir = config.get("wiki_dir", "./wiki/")
    wiki_count = 0
    if os.path.isdir(wiki_dir):
        wiki_count = len(
            [f for f in os.listdir(wiki_dir) if f.endswith((".md", ".txt"))]
        )

    statuses = []
    for app in APPS:
        status = DashboardAppStatus(
            name=app["name"],
            icon=app["icon"],
            description=app["description"],
            status="ready",
        )
        if app["name"] == "Wiki":
            status.description = f"{wiki_count} wiki files found"
        statuses.append(status)

    providers = config.get("providers", [])
    has_api_key = any(p.get("api_key") for p in providers)
    return {"apps": statuses, "config_valid": has_api_key}
