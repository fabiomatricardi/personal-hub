import os
import sys
import shutil
import subprocess

APP_NAME = "MyHub"
MAIN_ENTRY = "backend/main.py"


def build():
    for d in ["build", "dist"]:
        if os.path.exists(d):
            try:
                shutil.rmtree(d)
            except PermissionError:
                print(f"Warning: Could not remove {d} (may be in use). Retrying...")
                import time
                time.sleep(2)
                try:
                    shutil.rmtree(d)
                except PermissionError:
                    print(f"ERROR: Cannot remove {d}. Close any running instances and try again.")
                    sys.exit(1)

    subprocess.run("npm install", cwd="frontend", shell=True, check=True)
    subprocess.run("npm run build", cwd="frontend", shell=True, check=True)

    backend_packages = []
    for item in os.listdir("backend"):
        if os.path.isdir(os.path.join("backend", item)) and not item.startswith("_"):
            backend_packages.append(f"backend.{item}")

    data_args = []
    if os.path.isdir("frontend/dist"):
        data_args += ["--add-data", "frontend/dist;frontend/dist"]
    if os.path.isdir("wiki"):
        data_args += ["--add-data", "wiki;wiki"]

    hidden_imports = [
        "uvicorn.logging",
        "uvicorn.loops",
        "uvicorn.loops.auto",
        "uvicorn.protocols",
        "uvicorn.protocols.http",
        "uvicorn.protocols.http.auto",
        "uvicorn.protocols.websockets",
        "uvicorn.protocols.websockets.auto",
        "uvicorn.lifespan",
        "uvicorn.lifespan.on",
        "starlette",
        "starlette.routing",
        "starlette.responses",
        "starlette.middleware",
        "starlette.middleware.cors",
        "pydantic",
        "pydantic.fields",
        "multipart",
        "telegram",
        "telegram.ext",
        "apscheduler",
        "apscheduler.schedulers",
        "apscheduler.triggers",
        "apscheduler.triggers.cron",
        "bs4",
        "lxml",
        "lxml.etree",
    ]

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--noconsole",
        "--name", APP_NAME,
        *[arg for pkg in backend_packages for arg in ("--hidden-import", pkg)],
        *[arg for hi in hidden_imports for arg in ("--hidden-import", hi)],
        *data_args,
        MAIN_ENTRY,
    ]

    print(f"Building {APP_NAME}.exe ...")
    subprocess.run(cmd, check=True)
    print(f"Done: dist/{APP_NAME}.exe")


if __name__ == "__main__":
    build()
