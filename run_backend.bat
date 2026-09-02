@echo off
title Douyin Backend API Server
color 0A
echo ========================================================
echo   ?? DANG KHOI CHAY DOUYIN BACKEND SERVER (Port 8000)...
echo ========================================================
echo.
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
pause
