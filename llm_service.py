import os
from typing import List, Dict, Any
import google.generativeai as genai
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

class LLMService:
    """Google Gemini LLM 서비스"""
    
    def __init__(self, api_key: str = None):
        """
        Args:
            api_key: Google AI API 키 (None이면 .env에서 로드)
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY가 설정되지 않았습니다.")
        
        # Gemini 설정
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
    
    def generate_answer_with_sources(self, question: str, similar_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        질문과 관련 청크들을 기반으로 답변을 생성합니다.
        
        Args:
            question: 사용자 질문
            similar_chunks: 관련된 텍스트 청크들
            
        Returns:
            답변과 소스 정보를 포함한 딕셔너리
        """
        try:
            # 관련 텍스트들을 결합
            context_text = "\n\n".join([chunk["text"] for chunk in similar_chunks])
            
            # 향상된 프롬프트 생성
            prompt = self._create_enhanced_prompt(question, context_text)
            
            # 답변 생성
            response = self.model.generate_content(prompt)
            
            # 소스 정보 생성
            sources = []
            for i, chunk in enumerate(similar_chunks):
                # 청크에서 핵심 부분 추출 (처음 200자)
                snippet = chunk["text"][:200] + "..." if len(chunk["text"]) > 200 else chunk["text"]
                sources.append({
                    "chunk_id": chunk["chunk_id"],
                    "snippet": snippet
                })
            
            return {
                "answer": response.text,
                "source": sources
            }
            
        except Exception as e:
            print(f"LLM 서비스 오류: {str(e)}")
            return {
                "answer": "죄송합니다. 답변을 생성하는 중에 오류가 발생했습니다.",
                "source": []
            }
    
    def _create_enhanced_prompt(self, question: str, context_text: str) -> str:
        """향상된 프롬프트를 생성합니다."""
        prompt = f"""
PDF 문서 내용:
{context_text}

질문: {question}

지침:
- 질문에 직접적으로 답변하세요
- 문서 내용만 사용하세요
- 간결하게 답변하세요
- OCR 오류는 자동으로 수정하세요

답변:
"""
        return prompt 