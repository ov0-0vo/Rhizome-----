@echo off
echo Starting Rhizome Backend...
start cmd /k "uv run uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload"

echo Starting Rhizome Frontend...
cd frontend
start cmd /k "npm run dev"

echo.
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000
echo.
echo Press any key to exit this window (servers will continue running)...
pause >nul
