import os
from typing import Dict, Any, List
from pdf_processor import PDFProcessor
from vector_store import VectorStore
from llm_service import LLMService

class PDFQASystem:
    """PDF Q&A 시스템의 메인 클래스"""
    
    def __init__(self):
        """PDF Q&A 시스템을 초기화합니다."""
        self.pdf_processor = PDFProcessor(use_ocr=True)
        self.vector_store = VectorStore()
        self.llm_service = LLMService()
        
        # 인덱스 생성
        self.vector_store.create_index()
    
    def process_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """
        PDF 파일을 처리하고 벡터 저장소에 저장합니다.
        
        Args:
            pdf_path: PDF 파일 경로
            
        Returns:
            처리 결과 정보
        """
        try:
            # PDF에서 텍스트 추출 및 청킹
            chunks = self.pdf_processor.process_pdf(pdf_path)
            
            # 기존 벡터 삭제 (새로운 PDF로 교체)
            self.vector_store.clear_all_vectors()
            
            # 청크들을 벡터 저장소에 저장
            for chunk in chunks:
                self.vector_store.add_text(
                    text=chunk["text"],
                    metadata={"chunk_id": chunk["chunk_id"]}
                )
            
            return {
                "success": True,
                "chunks_processed": len(chunks),
                "message": f"{len(chunks)}개의 청크가 성공적으로 처리되었습니다."
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"PDF 처리 중 오류가 발생했습니다: {str(e)}"
            }
    
    def ask_question(self, question: str) -> Dict[str, Any]:
        """
        질문에 대한 답변을 생성합니다.
        
        Args:
            question: 사용자 질문
            
        Returns:
            답변과 소스 정보를 포함한 딕셔너리
        """
        try:
            # 유사한 텍스트 검색
            similar_chunks = self.vector_store.search_similar_text(question, top_k=5)
            
            if not similar_chunks:
                return {
                    "answer": "죄송합니다. 질문과 관련된 정보를 찾을 수 없습니다. PDF가 업로드되었는지 확인해주세요.",
                    "source": []
                }
            
            # LLM을 사용하여 답변 생성
            result = self.llm_service.generate_answer_with_sources(question, similar_chunks)
            
            return result
            
        except Exception as e:
            return {
                "answer": f"답변 생성 중 오류가 발생했습니다: {str(e)}",
                "source": []
            }
    
    def get_system_status(self) -> Dict[str, Any]:
        """시스템 상태를 반환합니다."""
        try:
            stats = self.vector_store.get_index_stats()
            return {
                "vector_count": stats.get("total_vector_count", 0),
                "index_dimension": stats.get("dimension", 384),
                "index_fullness": stats.get("index_fullness", 0)
            }
        except Exception as e:
            return {
                "error": str(e)
            } 