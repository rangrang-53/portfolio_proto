const API_BASE_URL = 'http://localhost:8000';

export interface QuestionRequest {
  question: string;
}

export interface QuestionResponse {
  answer: string;
  source: Array<{
    chunk_id: string;
    snippet: string;
  }>;
}

export interface UploadResponse {
  message: string;
  chunks_processed: number;
}

export interface SystemStatus {
  vector_count: number;
  index_dimension: number;
  index_fullness: number;
}

// PDF 업로드
export const uploadPDF = async (file: File): Promise<UploadResponse> => {
  const formData = new FormData();
  formData.append('file', file);

  try {
    const response = await fetch(`${API_BASE_URL}/upload-pdf`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json();
      const errorMessage = errorData.detail || 'PDF 업로드 중 오류가 발생했습니다.';
      
      // OCR 관련 오류 메시지 처리
      if (errorMessage.includes('OCR') || errorMessage.includes('Tesseract')) {
        throw new Error('OCR 처리 중 오류가 발생했습니다. Tesseract가 설치되어 있는지 확인해주세요.');
      } else if (errorMessage.includes('텍스트를 추출할 수 없습니다')) {
        throw new Error('PDF에서 텍스트를 추출할 수 없습니다. 스캔된 PDF이거나 텍스트가 없는 PDF일 수 있습니다. OCR 기능을 사용하려면 Tesseract를 설치해주세요.');
      } else {
        throw new Error('PDF 파일 형식이 올바르지 않거나 처리할 수 없습니다.');
      }
    }

    return await response.json();
  } catch (error) {
    if (error instanceof Error) {
      throw error;
    }
    throw new Error('PDF 업로드 중 오류가 발생했습니다.');
  }
};

// 질문하기
export const askQuestion = async (question: string): Promise<QuestionResponse> => {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 60000); // 60초 타임아웃

    const response = await fetch(`${API_BASE_URL}/ask-question`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ question }),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      if (response.status === 408) {
        throw new Error('요청 시간이 초과되었습니다. (60초 제한)');
      }
      throw new Error('질문 처리 중 오류가 발생했습니다.');
    }

    return await response.json();
  } catch (error) {
    if (error instanceof Error && error.name === 'AbortError') {
      throw new Error('요청 시간이 초과되었습니다. (60초 제한)');
    }
    throw new Error('질문 처리 중 오류가 발생했습니다.');
  }
};

// 시스템 상태 확인
export const getSystemStatus = async (): Promise<SystemStatus> => {
  try {
    const response = await fetch(`${API_BASE_URL}/system-status`);
    
    if (!response.ok) {
      throw new Error('시스템 상태 확인 중 오류가 발생했습니다.');
    }

    return await response.json();
  } catch (error) {
    throw new Error('시스템 상태 확인 중 오류가 발생했습니다.');
  }
}; 