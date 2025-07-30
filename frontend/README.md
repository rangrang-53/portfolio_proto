# PDF QA 시스템 프론트엔드

PDF 문서 기반 질의응답 시스템의 웹 인터페이스입니다.

## 기능

- 📄 **PDF 업로드**: 드래그 앤 드롭 또는 파일 선택으로 PDF 업로드
- 💬 **실시간 채팅**: 업로드된 PDF에 대한 질의응답
- 📋 **소스 참조**: 답변의 출처를 명확히 표시
- 📱 **반응형 디자인**: 모바일과 데스크톱 모두 지원
- 🔄 **실시간 상태**: 서버 연결 상태 실시간 확인

## 기술 스택

- **React 18** - 사용자 인터페이스
- **TypeScript** - 타입 안전성
- **Tailwind CSS** - 스타일링
- **Axios** - HTTP 클라이언트
- **Lucide React** - 아이콘

## 설치 및 실행

### 1. 의존성 설치

```bash
cd frontend
npm install
```

### 2. 개발 서버 실행

```bash
npm start
```

개발 서버가 `http://localhost:3000`에서 실행됩니다.

### 3. 프로덕션 빌드

```bash
npm run build
```

## 환경 변수

`.env` 파일을 생성하여 API 서버 URL을 설정할 수 있습니다:

```
REACT_APP_API_URL=http://localhost:8000
```

## 프로젝트 구조

```
src/
├── components/          # React 컴포넌트
│   ├── PDFUpload.tsx   # PDF 업로드 컴포넌트
│   ├── ChatInterface.tsx # 채팅 인터페이스
│   └── SystemStatus.tsx # 시스템 상태 표시
├── services/           # API 서비스
│   └── api.ts         # API 호출 함수들
├── types/             # TypeScript 타입 정의
│   └── index.ts       # 공통 타입들
├── App.tsx            # 메인 앱 컴포넌트
├── index.tsx          # 앱 진입점
└── index.css          # 글로벌 스타일
```

## 사용법

1. **PDF 업로드**: "문서 업로드" 탭에서 PDF 파일을 업로드합니다.
2. **질문하기**: "질의응답" 탭으로 이동하여 PDF 내용에 대해 질문합니다.
3. **답변 확인**: AI가 PDF 내용을 기반으로 답변을 생성합니다.
4. **소스 확인**: 답변 아래에 참고된 PDF 섹션들을 확인할 수 있습니다.

## 개발 가이드

### 새로운 컴포넌트 추가

```typescript
import React from 'react';

interface MyComponentProps {
  // props 타입 정의
}

const MyComponent: React.FC<MyComponentProps> = ({ /* props */ }) => {
  return (
    <div>
      {/* 컴포넌트 내용 */}
    </div>
  );
};

export default MyComponent;
```

### API 호출 추가

```typescript
// services/api.ts에 추가
export const newApiCall = async (data: any) => {
  try {
    const response = await api.post('/new-endpoint', data);
    return response.data;
  } catch (error) {
    throw new Error('API 호출 실패');
  }
};
```

## 라이센스

MIT License 