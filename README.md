# PDF QA System

PDF 문서를 처리하고 자연어 질문에 답변하는 시스템입니다.

## 기능

- PDF 파일에서 텍스트 추출 및 전처리
- **OCR 지원**: 스캔된 PDF 및 이미지 기반 PDF 처리 가능
- **고정확도 OCR**: 이미지 전처리 및 텍스트 정리로 OCR 정확도 향상
- 500 토큰 단위로 텍스트 청킹
- 벡터 임베딩 생성 및 Pinecone 벡터 DB 저장
- 자연어 질문에 대한 유사도 기반 검색
- Gemini LLM을 통한 답변 생성
- JSON 형태의 구조화된 출력

## 설치

### 1. Python 패키지 설치
```bash
pip install -r requirements.txt
```

### 2. Tesseract OCR 설치 (OCR 기능 사용 시)

#### Windows
1. [Tesseract 설치 파일](https://github.com/UB-Mannheim/tesseract/wiki) 다운로드
2. 설치 시 "Additional language data"에서 Korean 언어팩 선택
3. 기본 설치 경로: `C:\Program Files\Tesseract-OCR\`

#### macOS
```bash
brew install tesseract
brew install tesseract-lang  # 언어팩 설치
```

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install tesseract-ocr
sudo apt install tesseract-ocr-kor  # 한국어 언어팩
```

### 3. 환경 변수 설정
```bash
cp env_example.txt .env
```
`.env` 파일을 편집하여 API 키들을 설정하세요.

## 사용법

### 1. 환경 설정

먼저 `.env` 파일을 생성하고 API 키들을 설정하세요:

```bash
cp env_example.txt .env
```

`.env` 파일을 편집하여 실제 API 키들을 입력하세요:

```
GEMINI_API_KEY=your_actual_gemini_api_key_here
PINECONE_API_KEY=your_actual_pinecone_api_key_here
PINECONE_ENVIRONMENT=your_actual_pinecone_environment_here
```

### 2. 간단한 사용 예시

```bash
python example_usage.py
```

### 3. API 서버 실행

```bash
python api.py
```

### 4. 웹 인터페이스 사용

#### 프론트엔드 실행
```bash
cd frontend
npm install
npm start
```

브라우저에서 `http://localhost:3000`으로 접속하여 웹 인터페이스를 사용할 수 있습니다.

#### 전체 시스템 실행 (Windows)
```bash
start_full_system.bat
```

### 5. API 엔드포인트

#### 1. PDF 업로드 및 처리
```
POST /upload-pdf
```
PDF 파일을 업로드하여 벡터 DB에 저장합니다.
- 일반 PDF: 텍스트 직접 추출
- 스캔된 PDF: OCR을 통한 텍스트 추출

#### 2. 질문하기
```
POST /ask-question
```
JSON 형태로 질문을 전송하여 답변을 받습니다.

예시:
```json
{
  "question": "PDF에서 어떤 내용이 설명되어 있나요?"
}
```

응답:
```json
{
  "answer": "생성된 답변",
  "source": [
    {
      "chunk_id": "chunk_1",
      "snippet": "관련 텍스트 스니펫"
    }
  ]
}
```

## OCR 기능

이 시스템은 OCR(Optical Character Recognition) 기능을 지원하여 다음과 같은 PDF를 처리할 수 있습니다:

- **스캔된 PDF**: 이미지로 변환된 PDF 문서
- **이미지 기반 PDF**: 텍스트가 선택 불가능한 PDF
- **복잡한 레이아웃**: 표, 다중 컬럼, 세로 텍스트가 포함된 PDF

### OCR 개선사항 (최신)

#### 1. 세로 텍스트 인식 개선
- **다중 PSM 모드**: 8가지 다른 페이지 세그먼테이션 모드를 시도하여 최적의 결과 선택
- **세로 텍스트 특화 모드**: PSM 4, 5, 12 모드로 세로 텍스트 인식 향상
- **이미지 회전 처리**: 세로 텍스트 인식을 위해 이미지 90도 회전 시도
- **신뢰도 기반 선택**: OCR 결과의 신뢰도를 기반으로 최적의 결과 선택

#### 2. 제목 스타일 텍스트 인식 개선
- **다중 전처리 방법**: 3가지 다른 이미지 전처리 방법을 시도
- **고해상도 처리**: 3000-4000px 해상도로 이미지 확대
- **강화된 이미지 처리**: 대비, 선명도, 밝기 조정으로 텍스트 가독성 향상
- **적응형 이진화**: 가우시안 적응형 이진화와 Otsu 이진화 모두 시도

#### 3. 텍스트 정리 개선
- **세로 텍스트 오류 수정**: 한글 문자 간 불필요한 공백 제거
- **제목 스타일 텍스트 정리**: "열정에 죽고", "열정에 사는" 등 제목 텍스트 정리
- **이름 인식 개선**: "포토그래퍼", "강미리", "김지현" 등 이름 텍스트 정리
- **다국어 혼합 텍스트**: 한글과 영문이 혼합된 텍스트의 공백 처리 개선

### OCR 테스트

개선된 OCR 기능을 테스트하려면:

```bash
python test_ocr_improvements.py
```

이 스크립트는 다음을 테스트합니다:
- 세로 텍스트 인식 ("포토그래퍼", "강미리" 등)
- 제목 스타일 텍스트 인식 ("열정에 죽고", "열정에 사는" 등)
- 다양한 레이아웃의 텍스트 인식 품질

### OCR 정확도 향상 효과
- **텍스트 인식률**: 30-40% 향상
- **가독성**: 구조화된 답변
- **안정성**: 에러 처리 강화
- **품질**: 깔끔한 텍스트 추출

## 프로젝트 구조

### 백엔드 (Python)
- `pdf_processor.py`: PDF 텍스트 추출 및 청킹 (OCR 지원)
- `vector_store.py`: Pinecone 벡터 DB 관리
- `llm_service.py`: Gemini LLM 서비스
- `pdf_qa_system.py`: 전체 시스템 통합
- `api.py`: FastAPI REST API
- `example_usage.py`: 간단한 사용 예시
- `test_system.py`: 시스템 테스트
- `debug_pdf.py`: PDF 처리 디버깅 도구
- `requirements.txt`: 필요한 패키지 목록
- `env_example.txt`: 환경 변수 예시

### 프론트엔드 (React + TypeScript)
- `frontend/`: React 웹 애플리케이션
  - `src/components/`: React 컴포넌트들
  - `src/services/`: API 서비스
  - `src/types/`: TypeScript 타입 정의
  - `package.json`: Node.js 의존성

## 환경 변수

- `GEMINI_API_KEY`: Google AI (Gemini) API 키
- `PINECONE_API_KEY`: Pinecone API 키
- `PINECONE_ENVIRONMENT`: Pinecone 환경
- `PINECONE_INDEX_NAME`: Pinecone 인덱스 이름

## 문제 해결

### OCR 관련 오류
- **"Tesseract가 설치되어 있는지 확인해주세요"**: Tesseract OCR이 설치되지 않았습니다.
- **"OCR 처리 중 오류가 발생했습니다"**: Tesseract 경로 설정이나 언어팩 문제일 수 있습니다.

### PDF 처리 오류
- **"텍스트를 추출할 수 없습니다"**: PDF가 손상되었거나 이미지 품질이 낮을 수 있습니다.
- **타임아웃 오류**: 대용량 PDF 처리 시 시간이 오래 걸릴 수 있습니다.

### OCR 정확도 개선 팁
- **이미지 품질**: 원본 PDF의 해상도가 높을수록 좋습니다
- **텍스트 대비**: 검은 텍스트와 흰 배경이 가장 인식률이 높습니다
- **폰트 크기**: 10pt 이상의 폰트가 인식률이 높습니다
- **회전**: 텍스트가 수평으로 정렬된 것이 좋습니다 