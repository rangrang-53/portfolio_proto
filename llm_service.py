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

**핵심 지침:**
1. **질문에 직접적으로 답변하세요** - 질문에서 묻는 내용만 정확히 답변하세요.
2. **문서 내용만 사용하세요** - 주어진 문서에 있는 정보만으로 답변하세요.
3. **추측하지 마세요** - 문서에 없는 정보는 언급하지 마세요.
4. **간결하게 답변하세요** - 불필요한 정보는 제외하고 핵심만 답변하세요.

**OCR 텍스트 정리 규칙:**
- "APIz}} 60015" → "API 60015"
- "SMSCHstadAYsteyofyelatSe" → "SMS CH stadAY stey of yelatSe"
- "BoostShot" → "Boost Shot"
- "ClojaareraySey" → "Cloja areray Sey"
- "날짜 전부·** 2020년" → "날짜 정보: 2020년"
- 숫자와 단위 사이 공백 제거: "100 원" → "100원"

**답변 형식:**
질문에 대한 직접적이고 정확한 답변만 제공하세요. 문서에 해당 정보가 없다면 "문서에서 해당 정보를 찾을 수 없습니다."라고 답변하세요.

**주의사항:**
- 질문에서 묻는 특정 정보만 찾아서 답변하세요.
- 문서에 없는 정보는 절대 추측하거나 추가하지 마세요.
- OCR 오류가 있는 경우 가능한 한 정확하게 수정하여 답변하세요.

답변을 시작하세요:
"""
        return prompt 