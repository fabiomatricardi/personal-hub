@echo off
echo === MyHub Dev Launcher ===
echo.
echo Installing Python dependencies...
call uv sync
echo.
echo Installing frontend dependencies...
cd frontend && call npm install && cd ..
echo.
echo Starting dev server (frontend on :5173, backend on :8000)...
echo Frontend: http://localhost:5173
echo Backend:  http://localhost:8000
echo.
start "" cmd /c "cd frontend && npm run dev"
call uv run python -m backend.main
pause
