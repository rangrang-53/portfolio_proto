@echo off
echo PDF QA System - OCR 의존성 설치
echo =================================

echo.
echo 1. Python 패키지 설치 중...
pip install -r requirements.txt

echo.
echo 2. Tesseract OCR 설치 확인...
echo.
echo Tesseract가 설치되어 있지 않다면 다음 링크에서 다운로드하세요:
echo https://github.com/UB-Mannheim/tesseract/wiki
echo.
echo 설치 시 다음 사항을 확인하세요:
echo - "Additional language data"에서 Korean 언어팩 선택
echo - 기본 설치 경로: C:\Program Files\Tesseract-OCR\
echo.

echo 3. 설치 완료!
echo.
echo 이제 PDF QA 시스템을 실행할 수 있습니다.
echo start_full_system.bat 파일을 실행하세요.
pause 