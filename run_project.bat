@echo off
echo ================================================
echo   SmartDraft AI v2.0  —  Starting...
echo ================================================

REM Start backend
start cmd /k "cd backend && pip install -r requirements.txt --quiet && uvicorn main:app --reload --port 8000"

REM Wait 3 seconds for backend to boot
timeout /t 3 /nobreak > nul

REM Open frontend in browser (served via Python HTTP server)
start cmd /k "cd frontend && python -m http.server 5500"

timeout /t 2 /nobreak > nul
start http://127.0.0.1:5500

echo.
echo  Backend  : http://127.0.0.1:8000
echo  Frontend : http://127.0.0.1:5500
echo  API Docs : http://127.0.0.1:8000/docs
echo.
pause