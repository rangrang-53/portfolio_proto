#!/usr/bin/env python3
"""
PDF QA 시스템 사용 예시

이 스크립트는 PDF QA 시스템의 기본적인 사용법을 보여줍니다.
.env 파일에 API 키들이 설정되어 있어야 합니다.
"""

from pdf_qa_system import PDFQASystem

def main():
    """메인 함수"""
    print("🚀 PDF QA 시스템 사용 예시")
    print("=" * 50)
    
    try:
        # PDF QA 시스템 초기화 (.env 파일에서 API 키들을 자동으로 로드)
        print("📚 PDF QA 시스템을 초기화하는 중...")
        qa_system = PDFQASystem()
        print("✅ 시스템 초기화 완료!")
        
        # 시스템 통계 확인
        print("\n📊 시스템 통계:")
        stats = qa_system.get_index_stats()
        print(f"  - 총 벡터 수: {stats.get('total_vector_count', 0)}")
        print(f"  - 차원: {stats.get('dimension', 0)}")
        print(f"  - 인덱스 사용률: {stats.get('index_fullness', 0.0):.2%}")
        
        # 예시 질문
        print("\n🤔 예시 질문들:")
        example_questions = [
            "이 시스템은 무엇을 하는 시스템인가요?",
            "PDF 파일을 어떻게 처리하나요?",
            "벡터 데이터베이스는 어떤 역할을 하나요?"
        ]
        
        for i, question in enumerate(example_questions, 1):
            print(f"\n{i}. 질문: {question}")
            try:
                result = qa_system.ask_question(question)
                print(f"   답변: {result['answer']}")
                if result['source']:
                    print(f"   소스: {len(result['source'])}개 청크에서 찾음")
            except Exception as e:
                print(f"   오류: {str(e)}")
        
        print("\n🎉 예시 실행 완료!")
        print("\n💡 실제 사용을 위해서는:")
        print("   1. PDF 파일을 업로드하세요")
        print("   2. 질문을 입력하세요")
        print("   3. 시스템이 답변을 생성합니다")
        
    except ValueError as e:
        print(f"❌ 설정 오류: {str(e)}")
        print("💡 해결 방법:")
        print("   1. env_example.txt를 .env로 복사하세요")
        print("   2. .env 파일에 API 키들을 설정하세요")
        print("   3. 다시 실행하세요")
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")

if __name__ == "__main__":
    main() 