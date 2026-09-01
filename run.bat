@echo off
title INNOVEXA — Sovereign AI Workbench
color 0B

echo ====================================================
echo    INNOVEXA — Sovereign AI Workbench
echo    Starting all services...
echo ====================================================
echo.

cd /d %~dp0

echo [1/3] Starting FastAPI Backend...
start "INNOVEXA Backend" cmd /k "cd /d %~dp0 && .venv\Scripts\activate && uvicorn backend.main:app --reload"

echo [2/3] Waiting for backend to start...
timeout /t 6 /nobreak > nul

echo [3/3] Starting Streamlit Frontend...
start "INNOVEXA Frontend" cmd /k "cd /d %~dp0 && .venv\Scripts\activate && streamlit run frontend/app.py"

timeout /t 4 /nobreak > nul

echo Opening browser...
start http://localhost:8501

echo.
echo ====================================================
echo    INNOVEXA is LIVE!
echo    Frontend  : http://localhost:8501
echo    Backend   : http://localhost:8000
echo ====================================================
pause