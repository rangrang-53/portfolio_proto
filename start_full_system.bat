@echo off
echo 🚀 PDF QA 시스템 전체 시작
echo ================================
echo.

echo 📋 시스템 요구사항 확인:
echo - Node.js가 설치되어 있어야 합니다
echo - Python 3.8+가 설치되어 있어야 합니다
echo - .env 파일에 API 키들이 설정되어 있어야 합니다
echo.

echo 🔍 환경 설정 확인 중...
python check_setup.py

if %errorlevel% neq 0 (
    echo.
    echo ❌ 환경 설정에 문제가 있습니다.
    echo .env 파일을 확인하고 API 키들을 설정해주세요.
    pause
    exit /b 1
)

echo.
echo ✅ 환경 설정 확인 완료!
echo.

echo 🐍 백엔드 서버 시작 중...
echo 백엔드 서버가 http://localhost:8000 에서 실행됩니다.
echo.

start "PDF QA Backend" cmd /k "python api.py"

echo.
echo ⏳ 백엔드 서버 시작 대기 중...
timeout /t 5 /nobreak > nul

echo.
echo 🌐 프론트엔드 시작 중...
echo 프론트엔드가 http://localhost:3000 에서 실행됩니다.
echo.

cd frontend
call npm install
start "PDF QA Frontend" cmd /k "npm start"

echo.
echo 🎉 시스템이 성공적으로 시작되었습니다!
echo.
echo 📱 프론트엔드: http://localhost:3000
echo 🔧 백엔드 API: http://localhost:8000
echo 📚 API 문서: http://localhost:8000/docs
echo.

pause 