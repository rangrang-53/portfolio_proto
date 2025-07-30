import os
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import tempfile
import shutil

from pdf_qa_system import PDFQASystem

# 환경 변수 로드
load_dotenv()

# FastAPI 앱 생성
app = FastAPI(title="PDF Q&A API", version="1.0.0")

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

@app.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):
    """
    PDF 파일을 업로드하고 처리합니다.
    """
    try:
        # 파일 확장자 검증
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="PDF 파일만 업로드 가능합니다.")
        
        # 임시 파일로 저장
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # PDF 처리
            result = pdf_qa_system.process_pdf(temp_file_path)
            
            if result["success"]:
                return {
                    "message": result["message"],
                    "chunks_processed": result["chunks_processed"]
                }
            else:
                raise HTTPException(status_code=400, detail=result["message"])
                
        finally:
            # 임시 파일 삭제
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
    
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        if "OCR" in error_msg or "Tesseract" in error_msg:
            raise HTTPException(status_code=400, detail="OCR 처리 중 오류가 발생했습니다. Tesseract가 설치되어 있는지 확인해주세요.")
        elif "텍스트를 추출할 수 없습니다" in error_msg:
            raise HTTPException(status_code=400, detail="PDF에서 텍스트를 추출할 수 없습니다. 스캔된 PDF이거나 텍스트가 없는 PDF일 수 있습니다. OCR 기능을 사용하려면 Tesseract를 설치해주세요.")
        else:
            raise HTTPException(status_code=400, detail="PDF 파일 형식이 올바르지 않거나 처리할 수 없습니다.")

@app.post("/ask-question", response_model=QuestionResponse)
async def ask_question(request: QuestionRequest):
    """
    질문에 대한 답변을 생성합니다.
    """
    try:
        result = pdf_qa_system.ask_question(request.question)
        return QuestionResponse(
            answer=result["answer"],
            source=result["source"]
        )
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
    uvicorn.run(app, host="0.0.0.0", port=8000) 