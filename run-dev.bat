@echo off
echo === MyHub Dev Launcher ===
echo.
echo Installing Python dependencies...
call uv sync
echo.
echo Installing frontend dependencies...
cd frontend && call npm install && cd ..
echo.
echo Starting dev server (frontend on :5173, backend on :8999)...
start "" cmd /c "cd frontend && npm run dev"
call uv run python -m backend.main
start "" http://localhost:5173
pause
