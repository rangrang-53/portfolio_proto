import re
import os
import io
import cv2
import numpy as np
from typing import List, Dict, Any, Callable
from pypdf import PdfReader
import tiktoken
import tempfile

# OCR 관련 라이브러리들을 선택적으로 import
try:
    import pytesseract
    from PIL import Image, ImageEnhance, ImageFilter
    
    # pymupdf를 사용하여 PDF를 이미지로 변환
    try:
        import fitz  # PyMuPDF
        PYMUPDF_AVAILABLE = True
    except ImportError:
        PYMUPDF_AVAILABLE = False
        print("경고: PyMuPDF가 설치되지 않았습니다. pip install PyMuPDF로 설치하세요.")
    
    # pdf2image를 선택적으로 import (fallback)
    try:
        from pdf2image import convert_from_path
        PDF2IMAGE_AVAILABLE = True
    except ImportError:
        PDF2IMAGE_AVAILABLE = False
        print("경고: pdf2image가 설치되지 않았습니다. Poppler가 필요합니다.")
    
    OCR_AVAILABLE = True
    
    # Tesseract 경로 설정 (Windows)
    if os.name == 'nt':  # Windows
        # 일반적인 Tesseract 설치 경로들 확인
        tesseract_paths = [
            r'C:\Program Files\Tesseract-OCR\tesseract.exe',
            r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
            r'C:\Users\RANG\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'
        ]
        
        for path in tesseract_paths:
            if os.path.exists(path):
                pytesseract.pytesseract.tesseract_cmd = path
                print(f"Tesseract 경로 설정됨: {path}")
                break
        else:
            print("경고: Tesseract 경로를 찾을 수 없습니다. OCR 기능이 제한됩니다.")
            
except ImportError:
    OCR_AVAILABLE = False
    PYMUPDF_AVAILABLE = False
    PDF2IMAGE_AVAILABLE = False
    print("경고: OCR 라이브러리가 설치되지 않았습니다. 스캔된 PDF 처리가 제한됩니다.")


class PDFProcessor:
    """PDF 파일을 처리하고 텍스트를 청킹하는 클래스 (OCR 지원)"""
    
    def __init__(self, chunk_size: int = 500, use_ocr: bool = True):
        """
        Args:
            chunk_size: 각 청크의 토큰 수 (기본값: 500)
            use_ocr: OCR 사용 여부 (기본값: True)
        """
        self.chunk_size = chunk_size
        self.use_ocr = use_ocr and OCR_AVAILABLE and (PYMUPDF_AVAILABLE or PDF2IMAGE_AVAILABLE)
        self.tokenizer = tiktoken.get_encoding("cl100k_base")  # GPT-4 토크나이저
    
    def extract_text_from_pdf(self, pdf_path: str, progress_callback: Callable = None) -> str:
        """
        PDF 파일에서 텍스트를 추출합니다. (OCR 우선 사용)
        
        Args:
            pdf_path: PDF 파일 경로
            progress_callback: 진행상황 업데이트 콜백 함수
            
        Returns:
            추출된 텍스트
        """
        try:
            print(f"PDF 처리 시작: {pdf_path}")
            
            # 바로 OCR 사용 (텍스트 추출 건너뛰기)
            if self.use_ocr:
                print("OCR을 사용하여 텍스트를 추출합니다...")
                text = self._extract_text_with_ocr(pdf_path, progress_callback)
                print(f"OCR 텍스트 추출 결과: {len(text.strip())} 문자")
            else:
                # OCR이 비활성화된 경우에만 일반 텍스트 추출 사용
                text = self._extract_text_normally(pdf_path)
                print(f"일반 텍스트 추출 결과: {len(text.strip())} 문자")
            
            # 텍스트 정리
            text = self._clean_text(text)
            print(f"최종 정리된 텍스트: {len(text.strip())} 문자")
            
            # 디버깅을 위해 텍스트 샘플 출력
            if text.strip():
                print("\n--- 추출된 텍스트 샘플 (처음 300자) ---")
                print(text[:300])
                print("--- 텍스트 샘플 끝 ---\n")
            
            if not text.strip():
                if not OCR_AVAILABLE:
                    raise Exception("PDF에서 텍스트를 추출할 수 없습니다. 스캔된 PDF인 경우 Tesseract OCR을 설치해주세요.")
                elif not (PYMUPDF_AVAILABLE or PDF2IMAGE_AVAILABLE):
                    raise Exception("PDF에서 텍스트를 추출할 수 없습니다. 스캔된 PDF 처리를 위해 PyMuPDF를 설치해주세요: pip install PyMuPDF")
                else:
                    raise Exception("PDF에서 텍스트를 추출할 수 없습니다.")
            
            return text
            
        except Exception as e:
            print(f"PDF 텍스트 추출 오류: {str(e)}")
            raise
    
    def _extract_text_normally(self, pdf_path: str) -> str:
        """일반적인 방법으로 PDF에서 텍스트를 추출합니다."""
        reader = PdfReader(pdf_path)
        text = ""
        
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        
        return text
    
    def _extract_text_with_ocr(self, pdf_path: str, progress_callback: Callable = None) -> str:
        """OCR을 사용하여 PDF에서 텍스트를 추출합니다."""
        if not OCR_AVAILABLE:
            raise Exception("OCR 기능을 사용할 수 없습니다. pytesseract, Pillow 라이브러리를 설치해주세요.")
        
        if not (PYMUPDF_AVAILABLE or PDF2IMAGE_AVAILABLE):
            raise Exception("PDF를 이미지로 변환할 수 없습니다. PyMuPDF를 설치해주세요: pip install PyMuPDF")
        
        try:
            # Tesseract 설치 확인
            try:
                pytesseract.get_tesseract_version()
            except Exception:
                raise Exception("Tesseract OCR이 설치되지 않았습니다. https://github.com/UB-Mannheim/tesseract/wiki 에서 다운로드하세요.")
            
            # PDF를 이미지로 변환 (PyMuPDF 우선, fallback으로 pdf2image)
            images = self._convert_pdf_to_images(pdf_path)
            text = ""
            
            for i, image in enumerate(images):
                if progress_callback:
                    progress_callback(40 + (i / len(images)) * 10, f"페이지 {i+1} OCR 처리 중...", i+1)
                
                print(f"페이지 {i+1} OCR 처리 중...")
                
                # 이미지 전처리
                processed_image = self._preprocess_image(image)
                
                # 이미지에서 텍스트 추출 (향상된 설정)
                page_text = self._extract_text_with_enhanced_ocr(processed_image)
                text += page_text + "\n"
            
            return text
            
        except Exception as e:
            raise Exception(f"OCR 처리 중 오류 발생: {str(e)}")
    
    def _extract_text_with_enhanced_ocr(self, image: Image.Image) -> str:
        """
        향상된 OCR을 사용하여 이미지에서 텍스트를 추출합니다. (속도와 정확도 최적화)
        
        Args:
            image: PIL Image 객체
            
        Returns:
            추출된 텍스트
        """
        try:
            # 이미지 전처리 (속도 최적화)
            processed_image = self._preprocess_image_fast(image)
            
            # 한글 이름 인식에 최적화된 단일 OCR 설정 사용
            # PSM 6: 단일 블록 (한글 이름에 적합)
            # OEM 3: 기본 OCR 엔진 (속도와 정확도 균형)
            # kor+eng: 한글과 영어 모두 지원
            config = '--oem 3 --psm 6 -l kor+eng'
            
            # 원본 이미지로 먼저 시도
            text = pytesseract.image_to_string(image, config=config)
            
            # 텍스트 품질 평가
            confidence = self._evaluate_text_quality_fast(text)
            
            # 품질이 낮으면 전처리된 이미지로 재시도
            if confidence < 0.3:
                print("원본 이미지 품질이 낮아 전처리된 이미지로 재시도...")
                processed_text = pytesseract.image_to_string(processed_image, config=config)
                processed_confidence = self._evaluate_text_quality_fast(processed_text)
                
                # 더 나은 결과 선택
                if processed_confidence > confidence:
                    text = processed_text
                    confidence = processed_confidence
                    print(f"전처리된 이미지 사용 (품질 점수: {confidence:.2f})")
                else:
                    print(f"원본 이미지 유지 (품질 점수: {confidence:.2f})")
            else:
                print(f"원본 이미지 사용 (품질 점수: {confidence:.2f})")
            
            # 텍스트 정리 (속도 최적화)
            text = self._clean_text_fast(text)
            
            return text
            
        except Exception as e:
            print(f"OCR 처리 오류: {str(e)}")
            return ""
    

    
    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        OCR을 위한 이미지 전처리를 수행합니다. (속도 최적화 버전)
        
        Args:
            image: 원본 이미지
            
        Returns:
            전처리된 이미지
        """
        try:
            # 이미지를 numpy 배열로 변환
            img_array = np.array(image)
            
            # 그레이스케일 변환
            if len(img_array.shape) == 3:
                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            else:
                gray = img_array
            
            # 이미지 크기 조정 (적당한 해상도로 제한)
            height, width = gray.shape
            if width > 3000:  # 너무 큰 이미지는 축소
                scale_factor = 3000 / width
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)
                gray = cv2.resize(gray, (new_width, new_height), interpolation=cv2.INTER_AREA)
            elif width < 1500:  # 너무 작은 이미지는 확대
                scale_factor = 1500 / width
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)
                gray = cv2.resize(gray, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
            
            # 간단한 노이즈 제거
            denoised = cv2.medianBlur(gray, 3)
            
            # 적응형 이진화 (빠른 버전)
            binary = cv2.adaptiveThreshold(
                denoised, 
                255, 
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 
                15, 
                2
            )
            
            # numpy 배열을 PIL 이미지로 변환
            processed_image = Image.fromarray(binary)
            
            # 대비 향상 (적당한 강도)
            enhancer = ImageEnhance.Contrast(processed_image)
            processed_image = enhancer.enhance(1.3)
            
            return processed_image
            
        except Exception as e:
            print(f"이미지 전처리 오류: {str(e)}")
            return image
    
    def _preprocess_image_fast(self, image: Image.Image) -> Image.Image:
        """
        OCR을 위한 빠른 이미지 전처리를 수행합니다.
        
        Args:
            image: 원본 이미지
            
        Returns:
            전처리된 이미지
        """
        try:
            # 이미지를 numpy 배열로 변환
            img_array = np.array(image)
            
            # 그레이스케일 변환
            if len(img_array.shape) == 3:
                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            else:
                gray = img_array
            
            # 이미지 크기 조정 (적당한 해상도로 제한)
            height, width = gray.shape
            if width > 3000:  # 너무 큰 이미지는 축소
                scale_factor = 3000 / width
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)
                gray = cv2.resize(gray, (new_width, new_height), interpolation=cv2.INTER_AREA)
            elif width < 1500:  # 너무 작은 이미지는 확대
                scale_factor = 1500 / width
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)
                gray = cv2.resize(gray, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
            
            # 간단한 노이즈 제거
            denoised = cv2.medianBlur(gray, 3)
            
            # 적응형 이진화 (빠른 버전)
            binary = cv2.adaptiveThreshold(
                denoised, 
                255, 
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 
                15, 
                2
            )
            
            # numpy 배열을 PIL 이미지로 변환
            processed_image = Image.fromarray(binary)
            
            # 대비 향상 (적당한 강도)
            enhancer = ImageEnhance.Contrast(processed_image)
            processed_image = enhancer.enhance(1.3)
            
            return processed_image
            
        except Exception as e:
            print(f"이미지 전처리 오류: {str(e)}")
            return image
    
    def _evaluate_text_quality_fast(self, text: str) -> float:
        """
        텍스트 품질을 빠르게 평가합니다.
        
        Args:
            text: 평가할 텍스트
            
        Returns:
            품질 점수 (0.0 ~ 1.0)
        """
        if not text.strip():
            return 0.0
        
        # 한글과 영문 문자 수 계산
        korean_chars = len(re.findall(r'[가-힣]', text))
        english_chars = len(re.findall(r'[a-zA-Z]', text))
        total_chars = len(text.replace(' ', ''))
        
        if total_chars == 0:
            return 0.0
        
        # 기본 품질 점수
        basic_score = (korean_chars + english_chars) / total_chars
        
        # 한글 이름 패턴 점수 (간단한 버전)
        name_patterns = [
            r'[김이박최정강조윤장임한오서신권황안송류고문양손배조백허유남심노정하곽성차주우구신임나전민][가-힣]{1,3}\s*\(\d{2}\.\d{2}\.\d{2}\)',  # 이름 + 생년월일
            r'[김이박최정강조윤장임한오서신권황안송류고문양손배조백허유남심노정하곽성차주우구신임나전민][가-힣]{1,3}',  # 한글 이름
        ]
        
        name_score = 0
        for pattern in name_patterns:
            matches = re.findall(pattern, text)
            if matches:
                name_score += len(matches) * 0.2  # 이름 패턴당 0.2점 추가
        
        # 특수문자 비율 (간단한 평가)
        special_chars = len(re.findall(r'[^\w\s가-힣]', text))
        special_ratio = special_chars / max(total_chars, 1)
        special_score = max(0, 1.0 - special_ratio * 3)
        
        # 종합 점수 계산
        final_score = (basic_score * 0.6 + name_score * 0.3 + special_score * 0.1)
        
        return min(final_score, 1.0)
    
    def _clean_text(self, text: str) -> str:
        """
        추출된 텍스트를 정리합니다. (속도 최적화 버전)
        
        Args:
            text: 원본 텍스트
            
        Returns:
            정리된 텍스트
        """
        if not text.strip():
            return ""
        
        # 기본 정리
        # 불필요한 공백 제거
        text = re.sub(r'\s+', ' ', text)
        
        # 페이지 번호 제거
        text = re.sub(r'\b\d+\s*페이지?\b', '', text, flags=re.IGNORECASE)
        
        # 핵심적인 한글 이름 수정 패턴들
        # 1. 한글 사이 공백 제거
        text = re.sub(r'([가-힣])\s+([가-힣])', r'\1\2', text)
        
        # 2. 이름 + 생년월일 패턴 정리
        text = re.sub(r'([가-힣]+)\s*\((\d{2}\.\d{2}\.\d{2})\)', r'\1 (\2)', text)
        
        # 3. 성씨 + 이름 패턴에서 공백 제거
        text = re.sub(r'([김이박최정강조윤장임한오서신권황안송류고문양손배조백허유남심노정하곽성차주우구신임나전민])\s*([가-힣]{1,3})', r'\1\2', text)
        
        # 4. 일반적인 한글 OCR 오류 수정 (핵심적인 것들만)
        name_corrections = {
            r'이\s*름': '이름',
            r'생\s*년': '생년',
            r'월\s*일': '월일',
            r'연\s*락': '연락',
            r'이\s*메': '이메',
            r'개\s*발': '개발',
            r'이\s*력': '이력',
            r'자\s*기': '자기',
            r'소\s*개': '소개',
            r'경\s*력': '경력',
            r'학\s*력': '학력',
            r'기\s*술': '기술',
        }
        
        # 이름 오류 수정 적용
        for wrong_pattern, correct_text in name_corrections.items():
            text = re.sub(wrong_pattern, correct_text, text)
        
        # 연속된 공백 정리
        text = re.sub(r'\s+', ' ', text)
        
        # 문장 시작과 끝의 공백 제거
        text = text.strip()
        
        return text
    
    def _clean_text_fast(self, text: str) -> str:
        """
        추출된 텍스트를 빠르게 정리합니다. (핵심적인 수정만)
        
        Args:
            text: 원본 텍스트
            
        Returns:
            정리된 텍스트
        """
        if not text.strip():
            return ""
        
        # 기본 정리
        # 불필요한 공백 제거
        text = re.sub(r'\s+', ' ', text)
        
        # 페이지 번호 제거
        text = re.sub(r'\b\d+\s*페이지?\b', '', text, flags=re.IGNORECASE)
        
        # 핵심적인 한글 이름 수정 패턴들
        # 1. 한글 사이 공백 제거 (기본적인 것만)
        text = re.sub(r'([가-힣])\s+([가-힣])', r'\1\2', text)
        
        # 2. 이름 + 생년월일 패턴 정리
        text = re.sub(r'([가-힣]+)\s*\((\d{2}\.\d{2}\.\d{2})\)', r'\1 (\2)', text)
        
        # 3. 일반적인 한글 OCR 오류 수정 (핵심적인 것들만)
        name_corrections = {
            r'이\s*름': '이름',
            r'생\s*년': '생년',
            r'월\s*일': '월일',
            r'연\s*락': '연락',
            r'이\s*메': '이메',
            r'개\s*발': '개발',
            r'이\s*력': '이력',
            r'자\s*기': '자기',
            r'소\s*개': '소개',
            r'경\s*력': '경력',
            r'학\s*력': '학력',
            r'기\s*술': '기술',
        }
        
        # 이름 오류 수정 적용
        for wrong_pattern, correct_text in name_corrections.items():
            text = re.sub(wrong_pattern, correct_text, text)
        
        # 4. 성씨 + 이름 패턴에서 공백 제거
        text = re.sub(r'([김이박최정강조윤장임한오서신권황안송류고문양손배조백허유남심노정하곽성차주우구신임나전민])\s*([가-힣]{1,3})', r'\1\2', text)
        
        # 연속된 공백 정리
        text = re.sub(r'\s+', ' ', text)
        
        # 문장 시작과 끝의 공백 제거
        text = text.strip()
        
        return text
    
    def chunk_text(self, text: str) -> List[Dict[str, Any]]:
        """
        텍스트를 지정된 토큰 크기로 청킹합니다. (이름 정보 포함 개선)
        
        Args:
            text: 청킹할 텍스트
            
        Returns:
            청킹된 텍스트 섹션들의 리스트
        """
        # 텍스트를 문장 단위로 분할 (짧은 문장도 포함)
        sentences = self._split_into_sentences_with_names(text)
        
        chunks = []
        current_chunk = ""
        current_tokens = 0
        chunk_id = 0
        
        for sentence in sentences:
            sentence_tokens = len(self.tokenizer.encode(sentence))
            
            # 현재 청크에 문장을 추가할 수 있는지 확인
            if current_tokens + sentence_tokens <= self.chunk_size:
                current_chunk += sentence + " "
                current_tokens += sentence_tokens
            else:
                # 현재 청크가 완성되면 저장
                if current_chunk.strip():
                    chunks.append({
                        "chunk_id": f"chunk_{chunk_id}",
                        "text": current_chunk.strip(),
                        "token_count": current_tokens
                    })
                    chunk_id += 1
                
                # 새로운 청크 시작
                current_chunk = sentence + " "
                current_tokens = sentence_tokens
        
        # 마지막 청크 추가
        if current_chunk.strip():
            chunks.append({
                "chunk_id": f"chunk_{chunk_id}",
                "text": current_chunk.strip(),
                "token_count": current_tokens
            })
        
        return chunks
    
    def _split_into_sentences_with_names(self, text: str) -> List[str]:
        """
        텍스트를 문장 단위로 분할합니다. (이름 정보 포함 개선)
        
        Args:
            text: 분할할 텍스트
            
        Returns:
            문장들의 리스트
        """
        # 한글 이름 패턴을 먼저 찾아서 별도로 처리
        name_patterns = [
            r'[김이박최정강조윤장임한오서신권황안송류고문양손배조백허유남심노정하곽성차주우구신임나전민][가-힣]{1,3}\s*\(\d{2}\.\d{2}\.\d{2}\)',  # 이름 + 생년월일
            r'[김이박최정강조윤장임한오서신권황안송류고문양손배조백허유남심노정하곽성차주우구신임나전민][가-힣]{1,3}',  # 한글 이름
            r'[가-힣]{2,4}\s*\(\d{2}\.\d{2}\.\d{2}\)',  # 이름 + 생년월일 (일반)
        ]
        
        # 이름 패턴들을 별도로 추출
        name_sentences = []
        for pattern in name_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                name_sentences.append(match.strip())
        
        # 문장 끝 패턴 (마침표, 느낌표, 물음표, 줄바꿈)
        sentence_end_pattern = r'[.!?\n]+'
        
        # 텍스트를 문장으로 분할
        sentences = re.split(sentence_end_pattern, text)
        
        # 빈 문장 제거 및 정리 (길이 제한 완화)
        cleaned_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and len(sentence) > 3:  # 3자 이상이면 포함 (이름 포함)
                cleaned_sentences.append(sentence)
        
        # 이름 문장들을 앞쪽에 추가 (중복 제거)
        all_sentences = []
        seen_sentences = set()
        
        # 이름 문장들을 먼저 추가
        for name_sentence in name_sentences:
            if name_sentence not in seen_sentences:
                all_sentences.append(name_sentence)
                seen_sentences.add(name_sentence)
        
        # 일반 문장들 추가
        for sentence in cleaned_sentences:
            if sentence not in seen_sentences:
                all_sentences.append(sentence)
                seen_sentences.add(sentence)
        
        return all_sentences
    
    def process_pdf(self, pdf_path: str, progress_callback: Callable = None) -> List[Dict[str, Any]]:
        """
        PDF 파일을 처리하여 청킹된 텍스트 섹션들을 반환합니다.
        
        Args:
            pdf_path: PDF 파일 경로
            progress_callback: 진행상황 업데이트 콜백 함수 (progress, step, current_page)
            
        Returns:
            청킹된 텍스트 섹션들의 리스트
        """
        # PDF에서 텍스트 추출
        text = self.extract_text_from_pdf(pdf_path, progress_callback)
        
        if progress_callback:
            progress_callback(50, "텍스트 청킹 중...", 0)
        
        # 텍스트를 청킹
        chunks = self.chunk_text(text)
        
        if progress_callback:
            progress_callback(60, f"{len(chunks)}개 청크 생성 완료", 0)
        
        return chunks

    def _convert_pdf_to_images(self, pdf_path: str) -> List[Image.Image]:
        """PDF를 이미지로 변환합니다."""
        if PYMUPDF_AVAILABLE:
            return self._convert_with_pymupdf(pdf_path)
        elif PDF2IMAGE_AVAILABLE:
            return convert_from_path(pdf_path)
        else:
            raise Exception("PDF를 이미지로 변환할 수 있는 라이브러리가 없습니다.")
    
    def _convert_with_pymupdf(self, pdf_path: str) -> List[Image.Image]:
        """PyMuPDF를 사용하여 PDF를 이미지로 변환합니다. (속도 최적화)"""
        doc = fitz.open(pdf_path)
        images = []
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            # 적당한 해상도로 렌더링 (2x 확대 - 속도와 품질 균형)
            mat = fitz.Matrix(2.0, 2.0)
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("ppm")
            img = Image.open(io.BytesIO(img_data))
            images.append(img)
        
        doc.close()
        return images 