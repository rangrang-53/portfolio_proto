import os
import asyncio
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import tempfile
import shutil
import threading
import time

from pdf_qa_system import PDFQASystem

# 환경 변수 로드
load_dotenv()

# 진행상황 추적을 위한 전역 변수
processing_status = {
    "is_processing": False,
    "progress": 0,
    "current_step": "",
    "total_pages": 0,
    "current_page": 0
}

# 진행상황 업데이트 함수
def update_progress(progress: int, step: str = "", current_page: int = 0, total_pages: int = 0):
    global processing_status
    try:
        processing_status["progress"] = max(0, min(100, progress))  # 0-100 범위로 제한
        processing_status["current_step"] = step
        processing_status["current_page"] = max(0, current_page)
        processing_status["total_pages"] = max(0, total_pages)
        print(f"진행상황 업데이트: {progress}% - {step} (페이지: {current_page}/{total_pages})")
    except Exception as e:
        print(f"진행상황 업데이트 오류: {e}")
        # 오류 발생 시에도 기본값으로 설정
        processing_status["progress"] = 0
        processing_status["current_step"] = "오류 발생"
        processing_status["current_page"] = 0
        processing_status["total_pages"] = 0

# FastAPI 앱 생성 (파일 크기 제한 설정)
app = FastAPI(
    title="PDF Q&A API", 
    version="1.0.0",
    # 파일 업로드 크기 제한 설정 (100MB)
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# PDF Q&A 시스템 인스턴스
pdf_qa_system = PDFQASystem()

class QuestionRequest(BaseModel):
    question: str

class QuestionResponse(BaseModel):
    answer: str
    source: list

class ProgressResponse(BaseModel):
    is_processing: bool
    progress: int
    current_step: str
    current_page: int
    total_pages: int

@app.get("/processing-status")
async def get_processing_status():
    """
    현재 PDF 처리 진행상황을 반환합니다.
    """
    global processing_status
    return ProgressResponse(**processing_status)

@app.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):  # 파일 크기 제한 제거
    """
    PDF 파일을 업로드하고 처리합니다.
    """
    global processing_status
    
    try:
        print(f"PDF 업로드 시작: {file.filename}")
        
        # 진행상황 초기화
        processing_status["is_processing"] = True
        processing_status["progress"] = 0
        processing_status["current_step"] = "파일 검증 중..."
        processing_status["current_page"] = 0
        processing_status["total_pages"] = 0
        
        # 파일 확장자 검증
        if not file.filename.lower().endswith('.pdf'):
            processing_status["is_processing"] = False
            print(f"잘못된 파일 형식: {file.filename}")
            raise HTTPException(status_code=400, detail="PDF 파일만 업로드 가능합니다.")
        
        # 파일 크기 검증 (100MB)
        content = await file.read()
        if len(content) > 100 * 1024 * 1024:  # 100MB
            processing_status["is_processing"] = False
            print(f"파일 크기 초과: {len(content)} bytes")
            raise HTTPException(status_code=400, detail="파일 크기가 100MB를 초과합니다.")
        
        print(f"파일 검증 완료: {len(content)} bytes")
        update_progress(10, "파일 저장 중...")
        
        # 임시 파일로 저장
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        print(f"임시 파일 생성: {temp_file_path}")
        
        try:
            update_progress(20, "PDF 분석 시작...")
            
            # PDF 처리 (진행상황 추적 포함)
            def process_with_progress():
                try:
                    print("PDF 처리 시작...")
                    
                    # PDF 페이지 수 확인 (안전한 방법)
                    total_pages = 0
                    try:
                        import fitz
                        doc = fitz.open(temp_file_path)
                        total_pages = len(doc)
                        doc.close()
                        print(f"PDF 페이지 수: {total_pages}")
                    except Exception as e:
                        print(f"PDF 페이지 수 확인 오류: {e}")
                        total_pages = 1  # 기본값
                    
                    update_progress(30, f"총 {total_pages}페이지 분석 중...", 0, total_pages)
                    
                    # 진행상황 콜백 함수 정의
                    def progress_callback(progress: int, step: str, current_page: int = 0):
                        try:
                            update_progress(progress, step, current_page, total_pages)
                            print(f"진행상황 업데이트: {progress}% - {step}")
                        except Exception as e:
                            print(f"진행상황 업데이트 오류: {e}")
                    
                    # PDF 처리 (진행상황 업데이트 포함)
                    print("PDF QA 시스템 처리 시작...")
                    result = pdf_qa_system.process_pdf(temp_file_path, progress_callback)
                    
                    print(f"PDF 처리 결과: {result}")
                    
                    # 진행상황을 단계별로 업데이트
                    if result["success"]:
                        update_progress(90, "처리 완료 중...", total_pages, total_pages)
                        time.sleep(0.5)  # 완료 메시지 표시를 위한 짧은 지연
                        update_progress(100, "완료!", total_pages, total_pages)
                        return result
                    else:
                        update_progress(0, "처리 실패", 0, 0)
                        return result
                        
                except Exception as e:
                    print(f"PDF 처리 중 오류: {e}")
                    import traceback
                    traceback.print_exc()
                    update_progress(0, f"오류 발생: {str(e)}", 0, 0)
                    raise e
            
            # 별도 스레드에서 처리
            print("비동기 PDF 처리 시작...")
            result = await asyncio.to_thread(process_with_progress)
            
            if result["success"]:
                print("PDF 업로드 성공")
                return {
                    "message": result["message"],
                    "chunks_processed": result["chunks_processed"]
                }
            else:
                print(f"PDF 처리 실패: {result['message']}")
                raise HTTPException(status_code=400, detail=result["message"])
                
        finally:
            # 임시 파일 삭제
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
                print(f"임시 파일 삭제: {temp_file_path}")
            # 처리 완료 후 상태 초기화
            processing_status["is_processing"] = False
    
    except HTTPException:
        processing_status["is_processing"] = False
        raise
    except Exception as e:
        processing_status["is_processing"] = False
        print(f"PDF 업로드 중 예상치 못한 오류: {e}")
        import traceback
        traceback.print_exc()
        error_msg = str(e)
        if "OCR" in error_msg or "Tesseract" in error_msg:
            raise HTTPException(status_code=400, detail="OCR 처리 중 오류가 발생했습니다. Tesseract가 설치되어 있는지 확인해주세요.")
        elif "텍스트를 추출할 수 없습니다" in error_msg:
            raise HTTPException(status_code=400, detail="PDF에서 텍스트를 추출할 수 없습니다. 스캔된 PDF이거나 텍스트가 없는 PDF일 수 있습니다. OCR 기능을 사용하려면 Tesseract를 설치해주세요.")
        else:
            raise HTTPException(status_code=400, detail=f"PDF 파일 형식이 올바르지 않거나 처리할 수 없습니다. 오류: {error_msg}")

@app.post("/ask-question", response_model=QuestionResponse)
async def ask_question(request: QuestionRequest):
    """
    질문에 대한 답변을 생성합니다.
    """
    import asyncio
    
    try:
        # 60초 타임아웃으로 질문 처리
        result = await asyncio.wait_for(
            asyncio.to_thread(pdf_qa_system.ask_question, request.question),
            timeout=60.0
        )
        return QuestionResponse(
            answer=result["answer"],
            source=result["source"]
        )
    except asyncio.TimeoutError:
        raise HTTPException(status_code=408, detail="요청 시간이 초과되었습니다. (60초 제한)")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"답변 생성 중 오류가 발생했습니다: {str(e)}")

@app.get("/system-status")
async def get_system_status():
    """
    시스템 상태를 반환합니다.
    """
    try:
        status = pdf_qa_system.get_system_status()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"시스템 상태 조회 중 오류가 발생했습니다: {str(e)}")

@app.get("/")
async def root():
    """
    API 루트 엔드포인트
    """
    return {"message": "PDF Q&A API가 실행 중입니다."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000
    ) 