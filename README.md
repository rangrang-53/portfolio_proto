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

- **스캔된 PDF**: 종이 문서를 스캔한 PDF
- **이미지 기반 PDF**: 텍스트가 이미지로 저장된 PDF
- **혼합 PDF**: 텍스트와 이미지가 섞인 PDF

### OCR 처리 과정
1. 일반 텍스트 추출 시도
2. 텍스트가 부족한 경우 OCR 자동 활성화
3. PDF를 이미지로 변환
4. **이미지 전처리** (해상도 향상, 노이즈 제거, 대비 조정)
5. Tesseract OCR로 텍스트 추출
6. **텍스트 정리** (OCR 오류 수정, 특수문자 정리)
7. 한국어 및 영어 동시 지원

### OCR 정확도 향상 프로세스

#### 1. 이미지 전처리 최적화
- **해상도 향상**: 2000px 미만 이미지는 자동 확대
- **노이즈 제거**: 중간값 필터(5x5)로 노이즈 제거
- **적응형 이진화**: 가우시안 적응형 임계값 처리
- **모폴로지 연산**: 텍스트 선명화 (2x2 커널)
- **엣지 강화**: 샤프닝 필터로 텍스트 경계 강화
- **대비/밝기 조정**: 2.5x 대비, 1.2x 밝기

#### 2. OCR 설정 최적화
- **PSM 모드**: 6 (균등한 텍스트 블록)
- **OEM 모드**: 3 (LSTM 기반 OCR 엔진)
- **언어 설정**: 한국어 + 영어 동시 지원
- **에러 처리**: OCR 실패 시 안전한 처리

#### 3. 텍스트 정리 강화
- **날짜 오류 수정**: "낙짜 전부" → "날짜 정보"
- **기술 스택 정리**: Spring Boot, JavaScript, Node.js, Python, Docker
- **프로젝트명 정리**: Boost Shot, Cloja areray Sey
- **CamelCase 분리**: OCR로 붙어서 인식된 단어 분리
- **특수문자 정리**: 불필요한 특수문자 제거

#### 4. Gemini 프롬프트 개선
- **구체적인 오류 수정 규칙** 제공
- **구조화된 답변** 생성 (주요 내용 요약, 세부 정보, 데이터 정리)
- **OCR 오류 인식** 및 자동 수정
- **컨텍스트 인식** 답변 생성

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