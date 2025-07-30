#!/usr/bin/env python3
"""
PDF 처리 디버깅 스크립트
"""

import os
from pdf_processor import PDFProcessor
from vector_store import VectorStore
from llm_service import LLMService

def debug_pdf_processing(pdf_path: str):
    """PDF 처리 과정을 단계별로 디버깅합니다."""
    
    print("=" * 50)
    print("PDF 처리 디버깅 시작")
    print("=" * 50)
    
    # 1. PDF 텍스트 추출
    print("\n1. PDF 텍스트 추출 중...")
    processor = PDFProcessor(use_ocr=True)
    
    try:
        text = processor.extract_text_from_pdf(pdf_path)
        print(f"추출된 텍스트 길이: {len(text)} 문자")
        print("\n--- 추출된 텍스트 (처음 500자) ---")
        print(text[:500])
        print("\n--- 추출된 텍스트 (마지막 500자) ---")
        print(text[-500:])
        
    except Exception as e:
        print(f"텍스트 추출 오류: {e}")
        return
    
    # 2. 텍스트 청킹
    print("\n2. 텍스트 청킹 중...")
    chunks = processor.chunk_text(text)
    print(f"생성된 청크 수: {len(chunks)}")
    
    for i, chunk in enumerate(chunks[:3]):  # 처음 3개 청크만 출력
        print(f"\n--- 청크 {i+1} ---")
        print(f"청크 ID: {chunk['chunk_id']}")
        print(f"토큰 수: {chunk['token_count']}")
        print(f"텍스트 (처음 200자): {chunk['text'][:200]}...")
    
    # 3. 벡터 저장소에 저장
    print("\n3. 벡터 저장소에 저장 중...")
    vector_store = VectorStore()
    
    try:
        # 기존 인덱스 삭제 (테스트용)
        vector_store.delete_index()
        print("기존 인덱스 삭제됨")
    except:
        pass
    
    # 새 인덱스 생성
    vector_store.create_index()
    print("새 인덱스 생성됨")
    
    # 청크들을 벡터 저장소에 저장
    for chunk in chunks:
        vector_store.add_text(
            text=chunk["text"],
            metadata={"chunk_id": chunk["chunk_id"]}
        )
    
    print(f"{len(chunks)}개 청크가 벡터 저장소에 저장됨")
    
    # 4. 질문 테스트
    print("\n4. 질문 테스트...")
    test_question = "이 PDF의 내용은 뭐야?"
    
    # 유사한 청크 검색
    similar_chunks = vector_store.search_similar_text(test_question, top_k=3)
    print(f"검색된 유사 청크 수: {len(similar_chunks)}")
    
    for i, chunk in enumerate(similar_chunks):
        print(f"\n--- 유사 청크 {i+1} ---")
        print(f"청크 ID: {chunk['chunk_id']}")
        print(f"유사도 점수: {chunk.get('score', 'N/A')}")
        print(f"텍스트 (처음 200자): {chunk['text'][:200]}...")
    
    # 5. LLM 답변 생성
    print("\n5. LLM 답변 생성 중...")
    llm_service = LLMService()
    
    try:
        result = llm_service.generate_answer_with_sources(test_question, similar_chunks)
        print("\n--- 생성된 답변 ---")
        print(result['answer'])
        
        print("\n--- 사용된 소스 ---")
        for i, source in enumerate(result['source']):
            print(f"소스 {i+1} (ID: {source['chunk_id']}): {source['snippet'][:100]}...")
            
    except Exception as e:
        print(f"LLM 답변 생성 오류: {e}")
    
    print("\n" + "=" * 50)
    print("디버깅 완료")
    print("=" * 50)

if __name__ == "__main__":
    # PDF 파일 경로를 지정하세요
    pdf_path = input("PDF 파일 경로를 입력하세요: ").strip()
    
    if os.path.exists(pdf_path):
        debug_pdf_processing(pdf_path)
    else:
        print(f"파일을 찾을 수 없습니다: {pdf_path}") 