@echo off
echo PDF QA System - Poppler 설치 가이드
echo ====================================

echo.
echo Poppler는 PDF를 이미지로 변환하는 데 필요한 라이브러리입니다.
echo 스캔된 PDF 처리를 위해 필요합니다.
echo.

echo 1. Poppler 다운로드:
echo https://github.com/oschwartz10612/poppler-windows/releases
echo.

echo 2. 설치 과정:
echo - 최신 버전의 Release-xx.xx.x-0.zip 다운로드
echo - C:\poppler 폴더에 압축 해제
echo - 시스템 환경 변수 PATH에 C:\poppler\Library\bin 추가
echo.

echo 3. 환경 변수 설정:
echo - Windows 키 + R을 눌러 "sysdm.cpl" 실행
echo - "고급" 탭 클릭
echo - "환경 변수" 버튼 클릭
echo - "시스템 변수"에서 "Path" 선택 후 "편집" 클릭
echo - "새로 만들기" 클릭 후 "C:\poppler\Library\bin" 추가
echo - 모든 창에서 "확인" 클릭
echo.

echo 4. 설치 확인:
echo 설치 완료 후 새 명령 프롬프트를 열고 다음 명령어 실행:
echo pdfinfo --version
echo.

echo 5. 시스템 재시작:
echo 환경 변수 변경 후 시스템을 재시작하거나 새 터미널을 열어주세요.
echo.

pause 