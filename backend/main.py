import sys
import os

if getattr(sys, "frozen", False):
    sys.stdout = open(os.devnull, "w")
    sys.stderr = open(os.devnull, "w")

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

PORT = 8999


@asynccontextmanager
async def lifespan(app: FastAPI):
    from backend.services.cron_scheduler import init_scheduler
    init_scheduler()
    if getattr(sys, "frozen", False):
        import webbrowser
        webbrowser.open(f"http://localhost:{PORT}")
    yield


app = FastAPI(title="MyHub", version="1.2.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

from backend.routers import settings, dashboard, linkcard, wiki, tweetgen, telegram_digest, telegram_files, cron_dashboard
app.include_router(settings.router)
app.include_router(dashboard.router)
app.include_router(linkcard.router)
app.include_router(wiki.router)
app.include_router(tweetgen.router)
app.include_router(telegram_digest.router)
app.include_router(telegram_files.router)
app.include_router(cron_dashboard.router)


@app.post("/api/shutdown")
async def api_shutdown():
    import threading

    def _exit():
        import time

        time.sleep(0.5)
        os._exit(0)

    threading.Thread(target=_exit, daemon=True).start()
    return {"status": "shutting down"}


if getattr(sys, "frozen", False):
    frontend_dist = os.path.join(sys._MEIPASS, "frontend", "dist")
else:
    frontend_dist = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")

if os.path.isdir(frontend_dist):
    from fastapi.responses import FileResponse

    @app.api_route("/{full_path:path}", methods=["GET", "POST"])
    async def serve_spa(full_path: str):
        file_path = os.path.join(frontend_dist, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(frontend_dist, "index.html"))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=PORT)
