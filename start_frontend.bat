@echo off
echo 🚀 PDF QA 시스템 프론트엔드 시작 중...
echo.

cd frontend

echo 📦 의존성 설치 중...
call npm install

echo.
echo 🌐 개발 서버 시작 중...
echo 서버가 http://localhost:3000 에서 실행됩니다.
echo.

call npm start

pause 