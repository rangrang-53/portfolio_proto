#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OCR 개선사항 테스트 스크립트
세로 텍스트와 제목 스타일 텍스트 인식 개선을 테스트합니다.
"""

import os
import sys
from pdf_processor import PDFProcessor

def test_ocr_improvements():
    """OCR 개선사항을 테스트합니다."""
    print("=== OCR 개선사항 테스트 ===")
    
    # PDF 프로세서 초기화
    processor = PDFProcessor(use_ocr=True)
    
    # 테스트할 PDF 파일 경로
    test_pdf_path = input("테스트할 PDF 파일 경로를 입력하세요: ").strip()
    
    if not os.path.exists(test_pdf_path):
        print(f"오류: 파일을 찾을 수 없습니다: {test_pdf_path}")
        return
    
    try:
        print(f"\nPDF 파일 처리 중: {test_pdf_path}")
        
        # PDF에서 텍스트 추출
        extracted_text = processor.extract_text_from_pdf(test_pdf_path)
        
        print("\n=== 추출된 텍스트 ===")
        print(extracted_text)
        
        # 텍스트 청킹
        chunks = processor.chunk_text(extracted_text)
        
        print(f"\n=== 청킹 결과 ===")
        print(f"총 {len(chunks)}개의 청크가 생성되었습니다.")
        
        for i, chunk in enumerate(chunks[:3]):  # 처음 3개 청크만 표시
            print(f"\n청크 {i+1} (ID: {chunk['chunk_id']}):")
            print(f"토큰 수: {chunk['token_count']}")
            print(f"텍스트: {chunk['text'][:200]}...")
        
        # 세로 텍스트와 제목 스타일 텍스트 검색
        print("\n=== 세로 텍스트 및 제목 스타일 텍스트 검색 ===")
        
        # 검색할 키워드들
        search_keywords = [
            "포토그래퍼", "강미리", "김지현",
            "열정에 죽고", "열정에 사는",
            "photographer", "강미리", "김지현"
        ]
        
        found_keywords = []
        for keyword in search_keywords:
            if keyword.lower() in extracted_text.lower():
                found_keywords.append(keyword)
                print(f"✓ 발견: {keyword}")
            else:
                print(f"✗ 미발견: {keyword}")
        
        print(f"\n총 {len(found_keywords)}개의 키워드가 발견되었습니다.")
        
        if len(found_keywords) > 0:
            print("\n=== 발견된 키워드 주변 텍스트 ===")
            for keyword in found_keywords:
                # 키워드 주변 텍스트 찾기
                keyword_lower = keyword.lower()
                text_lower = extracted_text.lower()
                start_pos = text_lower.find(keyword_lower)
                
                if start_pos != -1:
                    # 키워드 주변 100자 추출
                    context_start = max(0, start_pos - 50)
                    context_end = min(len(extracted_text), start_pos + len(keyword) + 50)
                    context = extracted_text[context_start:context_end]
                    
                    print(f"\n'{keyword}' 주변 텍스트:")
                    print(f"...{context}...")
        
    except Exception as e:
        print(f"오류 발생: {str(e)}")
        return

if __name__ == "__main__":
    test_ocr_improvements() 