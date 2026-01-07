@echo off
echo Starting Laneige Ranking Insight Agent...
echo.

:: 백엔드 서버 시작 (가상환경 활성화 후 실행)
start "Backend Server" cmd /k "cd /d %~dp0 && venv\Scripts\activate && python -m uvicorn backend.api.main:app --reload --port 8000"

:: 대기
timeout /t 2 /nobreak > nul

:: 프론트엔드 서버 시작 (새 창에서)
start "Frontend Server" cmd /k "cd /d %~dp0\frontend && npm run dev"