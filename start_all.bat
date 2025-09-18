@echo off
echo ISPL 시스템 시작 중...
echo.

echo 1. 백엔드 서버 시작...
start "Backend Server" cmd /k "cd /d D:\APP\ispl_auto\backend && python main.py"

echo 2. 3초 대기...
timeout /t 3 /nobreak >nul

echo 3. 프론트엔드 서버 시작...
start "Frontend Server" cmd /k "cd /d D:\APP\ispl_auto\frontend && npm start"

echo.
echo ✅ 모든 서버가 시작되었습니다!
echo 백엔드: http://localhost:8000
echo 프론트엔드: http://localhost:3000
echo.
pause

