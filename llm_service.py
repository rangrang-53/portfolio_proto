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
당신은 PDF 문서를 기반으로 질문에 답변하는 전문 AI 어시스턴트입니다.

**주어진 문서 내용 (OCR로 추출된 원본 텍스트):**
{context_text}

**사용자 질문:**
{question}

**답변 지침:**
1. 주어진 문서 내용만을 기반으로 답변하세요.
2. 문서에 없는 정보는 추측하지 마세요.
3. OCR로 추출된 텍스트의 오타와 오류를 자동으로 수정하고 정리하세요.
4. 답변은 명확하고 구조화된 형태로 제공하세요.
5. 숫자, 날짜, 이름 등은 정확하게 인용하세요.
6. 한국어로 답변하되, 필요한 경우 영어 용어도 함께 표기하세요.

**OCR 텍스트 정리 규칙:**
- "APIz}} 60015" → "API 60015"
- "SMSCHstadAYsteyofyelatSe" → "SMS CH stadAY stey of yelatSe" (의미 있는 단어로 분리)
- "BoostShot" → "Boost Shot"
- "ClojaareraySey" → "Cloja areray Sey" (의미 있는 단어로 분리)
- "날짜 전부·** 2020년" → "날짜 정보: 2020년"
- 숫자와 단위 사이 공백 제거: "100 원" → "100원"
- 불필요한 특수문자 제거 및 정리

**답변 구조:**
1. **주요 내용 요약**: 문서의 핵심 내용을 간결하게 요약
2. **세부 정보**: 
   - 사용 기술/도구
   - 프로젝트 정보
   - 날짜/기간 정보
   - 기타 중요 정보
3. **데이터 정리**: OCR 오류가 수정된 정확한 정보
4. **참고사항**: 원본 텍스트의 품질이나 해석에 대한 주의사항

**주의사항:**
- OCR로 추출된 텍스트이므로 일부 오타가 있을 수 있습니다.
- 의미가 불분명한 단어나 구문은 원본 그대로 표시하되, 가능한 해석을 제시하세요.
- 기술 스택, 프로젝트명, 날짜 등은 정확하게 정리하여 제공하세요.
- 문서의 구조와 맥락을 고려하여 답변하세요.

답변을 시작하세요:
"""
        return prompt 