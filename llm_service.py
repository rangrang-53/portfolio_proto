import os
from typing import List, Dict, Any, Optional
import google.generativeai as genai
import requests
import json
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

class LLMService:
    """Google Gemini LLM 서비스 (Llama 4 폴백 지원)"""
    
    def __init__(self, api_key: str = None, use_fallback: bool = True, llama_api_key: str = None, llama_endpoint: str = None):
        """
        Args:
            api_key: Google AI API 키 (None이면 .env에서 로드)
            use_fallback: Llama 4 폴백 사용 여부
            llama_api_key: Llama API 키 (직접 전달)
            llama_endpoint: Llama API 엔드포인트 (직접 전달)
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.use_fallback = use_fallback
        
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY가 설정되지 않았습니다.")
        
        # Gemini 설정
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Llama 4 폴백 설정 (.env에서 로드 또는 직접 파라미터)
        if self.use_fallback:
            self.llama_api_key = llama_api_key or os.getenv("LLAMA_API_KEY")  # 직접 전달 또는 .env에서 로드
            self.llama_endpoint = llama_endpoint or "https://api.llama.meta.com/v1/chat/completions"
    
    def generate_answer_with_sources(self, question: str, similar_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        질문과 관련 청크들을 기반으로 답변을 생성합니다.
        Gemini 실패 시 Llama 4로 폴백합니다.
        
        Args:
            question: 사용자 질문
            similar_chunks: 관련된 텍스트 청크들
            
        Returns:
            답변과 소스 정보를 포함한 딕셔너리
        """
        try:
            # 관련 텍스트들을 결합 (길이 제한)
            context_text = self._combine_chunks_optimized(similar_chunks)
            
            # 간결한 프롬프트 생성
            prompt = self._create_optimized_prompt(question, context_text)
            
            # Gemini로 답변 생성 시도
            try:
                response = self.model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        max_output_tokens=500,  # 응답 길이 제한
                        temperature=0.3,  # 일관성 향상
                    )
                )
                
                answer = response.text
                model_used = "Gemini"
                
            except Exception as gemini_error:
                print(f"Gemini 오류: {str(gemini_error)}")
                
                # 폴백이 활성화되어 있으면 Llama 4 사용 (API 키 없어도 시도)
                if self.use_fallback:
                    try:
                        answer = self._generate_with_llama(prompt)
                        model_used = "Llama 4 (폴백)"
                    except Exception as llama_error:
                        print(f"Llama 4 폴백 오류: {str(llama_error)}")
                        answer = "죄송합니다. 답변을 생성하는 중에 오류가 발생했습니다."
                        model_used = "오류"
                else:
                    answer = "죄송합니다. 답변을 생성하는 중에 오류가 발생했습니다."
                    model_used = "오류"
            
            # 소스 정보 생성
            sources = []
            for i, chunk in enumerate(similar_chunks):
                # 청크에서 핵심 부분 추출 (처음 150자로 줄임)
                snippet = chunk["text"][:150] + "..." if len(chunk["text"]) > 150 else chunk["text"]
                sources.append({
                    "chunk_id": chunk["chunk_id"],
                    "snippet": snippet
                })
            
            return {
                "answer": answer,
                "source": sources,
                "model_used": model_used
            }
            
        except Exception as e:
            print(f"LLM 서비스 오류: {str(e)}")
            return {
                "answer": "죄송합니다. 답변을 생성하는 중에 오류가 발생했습니다.",
                "source": [],
                "model_used": "오류"
            }
    
    def _generate_with_llama(self, prompt: str) -> str:
        """Llama 4를 사용하여 답변을 생성합니다."""
        headers = {
            "Content-Type": "application/json"
        }
        
        # API 키가 있으면 Authorization 헤더 추가
        if self.llama_api_key:
            headers["Authorization"] = f"Bearer {self.llama_api_key}"
        
        data = {
            "model": "Llama-4-Scout-17B-16E",  # Meta Llama Scout 모델
            "messages": [
                {
                    "role": "system",
                    "content": "당신은 이력서, 포트폴리오, 경력기술서 등의 문서를 분석하는 AI PDF 분석가입니다. 문서 내용을 바탕으로 정확하고 가독성 높은 요약을 생성하세요."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 500,
            "temperature": 0.3,
            "stream": False
        }
        
        response = requests.post(
            self.llama_endpoint,
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["message"]["content"]
        else:
            raise Exception(f"Llama API 오류: {response.status_code} - {response.text}")
    
    def _combine_chunks_optimized(self, chunks: List[Dict[str, Any]]) -> str:
        """청크들을 최적화된 방식으로 결합합니다."""
        combined_text = ""
        max_length = 1500  # 최대 길이 제한
        
        for chunk in chunks:
            chunk_text = chunk["text"]
            if len(combined_text) + len(chunk_text) <= max_length:
                combined_text += chunk_text + "\n\n"
            else:
                # 남은 공간에 맞게 잘라서 추가
                remaining_space = max_length - len(combined_text)
                if remaining_space > 50:  # 최소 50자 이상 남은 경우만
                    combined_text += chunk_text[:remaining_space] + "..."
                break
        
        return combined_text.strip()
    
    def _create_optimized_prompt(self, question: str, context_text: str) -> str:
        """
        이력서 및 포트폴리오 중심 문서를 분석하고 가독성 높은 요약을 생성하는 AI 분석가용 프롬프트입니다.
        """
        prompt = f"""
당신은 이력서, 포트폴리오, 경력기술서 등의 문서를 분석하는 AI PDF 분석가입니다.  
문서 내용을 바탕으로 **정확하고 가독성 높은 요약**을 생성하세요.  
질문에 대한 답변은 반드시 아래 형식 지침을 따르세요.

[문서 내용]
{context_text}

[질문]
{question}

[출력 형식 지침]
- **단락 구분**: 주제별로 1~3문장 단위로 줄바꿈하세요.
- **중요 키워드 또는 핵심 문장**은 **굵게 표시**하세요. (예: **Java**, **SAGA 패턴**)
- **정보가 나열될 경우**, 번호(1, 2, 3...) 또는 글머리 기호(*)를 사용하세요.
- 출력은 반드시 한국어로 자연스럽게 작성하세요.
- 문서에 명시되지 않은 정보는 절대 추측하지 말고, "문서에 해당 정보가 없습니다."라고 명확히 답변하세요.

[예시 형식]
---

**1. 프로젝트 개요**  
이 프로젝트는 주문 및 결제 시스템을 구현한 것입니다. 주요 기술로는 **RabbitMQ**, **SAGA 패턴**, **Java** 등이 사용되었습니다.

**2. 기술 스택**  
* 백엔드: **Java**, **MySQL**, **Redis**  
* 인프라: **AWS**, **Terraform**, **GitHub Actions**

**3. 구현 기능**  
1. 주문 상태 이벤트 전환  
2. 이메일 인증 및 주소 저장  
3. 카카오맵 API 연동

---

위 예시처럼 명확하게 단락을 구분하고, 핵심은 강조하며, 목록은 구조적으로 표현하세요.

[답변 시작]
"""
        return prompt