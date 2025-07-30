import os
from dotenv import load_dotenv
from pdf_qa_system import PDFQASystem

# 환경 변수 로드
load_dotenv()

def test_pdf_qa_system():
    """PDF QA 시스템 테스트"""
    
    try:
        # PDF QA 시스템 초기화 (.env 파일에서 자동으로 API 키들을 로드)
        print("🔄 PDF QA 시스템 초기화 중...")
        qa_system = PDFQASystem()
        print("✅ PDF QA 시스템 초기화 완료")
        
        # 테스트 질문
        test_question = "이 시스템은 무엇을 하는 시스템인가요?"
        
        print(f"🤔 테스트 질문: {test_question}")
        
        # 답변 생성
        result = qa_system.ask_question(test_question)
        
        print("📝 답변:")
        print(f"답변: {result['answer']}")
        print(f"소스: {result['source']}")
        
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")

if __name__ == "__main__":
    test_pdf_qa_system() 