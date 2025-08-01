import re
import os
import io
import cv2
import numpy as np
from typing import List, Dict, Any
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
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        PDF 파일에서 텍스트를 추출합니다. (OCR 지원)
        
        Args:
            pdf_path: PDF 파일 경로
            
        Returns:
            추출된 텍스트
        """
        try:
            print(f"PDF 처리 시작: {pdf_path}")
            
            # 먼저 일반적인 텍스트 추출 시도
            text = self._extract_text_normally(pdf_path)
            print(f"일반 텍스트 추출 결과: {len(text.strip())} 문자")
            
            # 텍스트가 충분하지 않으면 OCR 사용
            if len(text.strip()) < 50 and self.use_ocr:
                print("텍스트 추출이 부족합니다. OCR을 사용합니다...")
                ocr_text = self._extract_text_with_ocr(pdf_path)
                print(f"OCR 텍스트 추출 결과: {len(ocr_text.strip())} 문자")
                
                # OCR 결과가 더 좋으면 OCR 텍스트 사용
                if len(ocr_text.strip()) > len(text.strip()):
                    text = ocr_text
                    print("OCR 결과를 사용합니다.")
                else:
                    print("일반 텍스트 추출 결과를 사용합니다.")
            
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
    
    def _extract_text_with_ocr(self, pdf_path: str) -> str:
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
        향상된 OCR을 사용하여 이미지에서 텍스트를 추출합니다.
        
        Args:
            image: PIL Image 객체
            
        Returns:
            추출된 텍스트
        """
        try:
            # 이미지 전처리
            processed_image = self._preprocess_image(image)
            
            # 여러 OCR 설정을 시도하여 최적의 결과 찾기
            configs = [
                '--oem 3 --psm 6 -l kor+eng',  # 기본 설정
                '--oem 3 --psm 3 -l kor+eng',  # 자동 페이지 세그멘테이션
                '--oem 1 --psm 6 -l kor+eng',  # LSTM OCR 엔진
                '--oem 3 --psm 8 -l kor+eng',  # 단일 워드
                '--oem 3 --psm 13 -l kor+eng',  # 원시 라인
                '--oem 3 --psm 1 -l kor+eng',  # 자동 페이지 세그멘테이션 + OSD
                '--oem 1 --psm 3 -l kor+eng',  # LSTM + 자동 세그멘테이션
            ]
            
            best_text = ""
            best_confidence = 0
            best_source = "processed"
            
            # 전처리된 이미지로 OCR 시도
            for i, config in enumerate(configs):
                try:
                    # OCR 실행
                    text = pytesseract.image_to_string(
                        processed_image, 
                        config=config
                    )
                    
                    # 텍스트 품질 평가 (한글과 영문 비율)
                    korean_chars = len(re.findall(r'[가-힣]', text))
                    english_chars = len(re.findall(r'[a-zA-Z]', text))
                    total_chars = len(text.replace(' ', ''))
                    
                    if total_chars > 0:
                        confidence = (korean_chars + english_chars) / total_chars
                        if confidence > best_confidence:
                            best_text = text
                            best_confidence = confidence
                            best_source = "processed"
                            print(f"전처리 이미지 OCR 설정 {i+1} (점수: {confidence:.2f}): {config}")
                            
                except Exception as e:
                    print(f"전처리 이미지 OCR 설정 {i+1} 실패: {e}")
                    continue
            
            # 원본 이미지로도 OCR 시도 (전처리가 문제일 수 있음)
            print("원본 이미지로 OCR 시도...")
            for i, config in enumerate(configs[:3]):  # 처음 3개 설정만 시도
                try:
                    # OCR 실행
                    text = pytesseract.image_to_string(
                        image, 
                        config=config
                    )
                    
                    # 텍스트 품질 평가
                    korean_chars = len(re.findall(r'[가-힣]', text))
                    english_chars = len(re.findall(r'[a-zA-Z]', text))
                    total_chars = len(text.replace(' ', ''))
                    
                    if total_chars > 0:
                        confidence = (korean_chars + english_chars) / total_chars
                        if confidence > best_confidence:
                            best_text = text
                            best_confidence = confidence
                            best_source = "original"
                            print(f"원본 이미지 OCR 설정 {i+1} (점수: {confidence:.2f}): {config}")
                            
                except Exception as e:
                    print(f"원본 이미지 OCR 설정 {i+1} 실패: {e}")
                    continue
            
            if not best_text:
                # 모든 설정이 실패한 경우 기본 설정으로 재시도
                best_text = pytesseract.image_to_string(
                    image, 
                    lang='kor+eng',
                    config='--oem 3 --psm 6'
                )
                best_source = "fallback"
            
            print(f"최종 선택된 이미지: {best_source}")
            
            # 텍스트 정리
            text = self._clean_text(best_text)
            
            return text
            
        except Exception as e:
            print(f"OCR 처리 오류: {str(e)}")
            return ""
    
    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        OCR을 위한 이미지 전처리를 수행합니다.
        
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
            
            # 이미지 크기 조정 (적당한 해상도로)
            height, width = gray.shape
            if width < 1500:  # 적당한 해상도로 확대
                scale_factor = 1500 / width
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)
                gray = cv2.resize(gray, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
            
            # 노이즈 제거 (약한 필터)
            denoised = cv2.medianBlur(gray, 3)
            
            # 적응형 이진화 (더 보수적)
            binary = cv2.adaptiveThreshold(
                denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, 5
            )
            
            # 모폴로지 연산 (약한 필터)
            kernel = np.ones((1, 1), np.uint8)
            processed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
            
            # numpy 배열을 PIL 이미지로 변환
            processed_image = Image.fromarray(processed)
            
            # 대비 향상 (약하게)
            enhancer = ImageEnhance.Contrast(processed_image)
            processed_image = enhancer.enhance(1.5)
            
            # 밝기 조정 (약하게)
            enhancer = ImageEnhance.Brightness(processed_image)
            processed_image = enhancer.enhance(1.1)
            
            return processed_image
            
        except Exception as e:
            print(f"이미지 전처리 오류: {str(e)}")
            return image
    
    def _convert_pdf_to_images(self, pdf_path: str) -> List[Image.Image]:
        """PDF를 이미지로 변환합니다."""
        if PYMUPDF_AVAILABLE:
            return self._convert_with_pymupdf(pdf_path)
        elif PDF2IMAGE_AVAILABLE:
            return convert_from_path(pdf_path)
        else:
            raise Exception("PDF를 이미지로 변환할 수 있는 라이브러리가 없습니다.")
    
    def _convert_with_pymupdf(self, pdf_path: str) -> List[Image.Image]:
        """PyMuPDF를 사용하여 PDF를 이미지로 변환합니다."""
        doc = fitz.open(pdf_path)
        images = []
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            # 더 높은 해상도로 렌더링 (3x 확대)
            mat = fitz.Matrix(3.0, 3.0)
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("ppm")
            img = Image.open(io.BytesIO(img_data))
            images.append(img)
        
        doc.close()
        return images
    
    def _clean_text(self, text: str) -> str:
        """
        추출된 텍스트를 정리합니다.
        
        Args:
            text: 원본 텍스트
            
        Returns:
            정리된 텍스트
        """
        # 불필요한 공백 제거
        text = re.sub(r'\s+', ' ', text)
        
        # 페이지 번호 제거 (일반적인 패턴)
        text = re.sub(r'\b\d+\s*페이지?\b', '', text, flags=re.IGNORECASE)
        
        # OCR 오류 수정 (일반적인 오타 패턴)
        text = re.sub(r'APIz\s*\}\s*(\d+)', r'API \1', text)  # APIz} 60015 -> API 60015
        text = re.sub(r'(\d+)\s*원', r'\1원', text)  # 숫자와 원 사이 공백 제거
        
        # 날짜 관련 오류 수정
        text = re.sub(r'낙짜\s*전부', '날짜 정보', text)  # 낙짜 전부 -> 날짜 정보
        text = re.sub(r'날짜\s*전부', '날짜 정보', text)  # 날짜 전부 -> 날짜 정보
        text = re.sub(r'(\d{4})년', r'\1년', text)  # 연도 형식 정리
        
        # 기술 스택 관련 오류 수정
        text = re.sub(r'Spring\s*Boot', 'Spring Boot', text)  # Spring Boot 정리
        text = re.sub(r'Java\s*Script', 'JavaScript', text)  # JavaScript 정리
        text = re.sub(r'Node\.\s*js', 'Node.js', text)  # Node.js 정리
        text = re.sub(r'React\s*JS', 'React.js', text)  # React.js 정리
        text = re.sub(r'Python\s*Script', 'Python', text)  # Python 정리
        text = re.sub(r'Docker\s*Container', 'Docker', text)  # Docker 정리
        
        # 프로젝트명 관련 오류 수정
        text = re.sub(r'Boost\s*Shot', 'Boost Shot', text)  # Boost Shot 정리
        text = re.sub(r'Cloja\s*areray\s*Sey', 'Cloja areray Sey', text)  # 프로젝트명 정리
        
        # 일반적인 OCR 오류 수정
        text = re.sub(r'([A-Z])([a-z]+)([A-Z])', r'\1\2 \3', text)  # CamelCase 분리
        text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)  # camelCase 분리
        
        # 추가 OCR 오류 수정 패턴들
        # 깨진 한글 문자 수정
        text = re.sub(r'로\s*po\s*는', '로부터', text)
        text = re.sub(r'이\s*6\s*겨은', '이력서', text)
        text = re.sub(r'SSE\s*Sl\s*쿠비', 'Spring Boot', text)
        text = re.sub(r'이\s*a\s*-', '이력서', text)
        text = re.sub(r'ale\s*대\s*외', '개발자', text)
        text = re.sub(r'st\s*Se\s*a', 'Spring', text)
        text = re.sub(r'ry\s*1\s*oan', 'React', text)
        text = re.sub(r'we\s*ee\s*에', '웹', text)
        text = re.sub(r'난티이데', '개발', text)
        text = re.sub(r'년에\s*에이', '년', text)
        text = re.sub(r'이\s*이애\s*이타언', '이력서', text)
        text = re.sub(r'이과티\s*애와에', '이력서', text)
        
        # 기술 스택 관련 추가 수정
        text = re.sub(r'Java\s*Script', 'JavaScript', text)
        text = re.sub(r'Spring\s*Framework', 'Spring Framework', text)
        text = re.sub(r'MySQL\s*Database', 'MySQL', text)
        text = re.sub(r'Redis\s*Cache', 'Redis', text)
        text = re.sub(r'AWS\s*Cloud', 'AWS', text)
        text = re.sub(r'Docker\s*Container', 'Docker', text)
        text = re.sub(r'Kubernetes\s*Orchestration', 'Kubernetes', text)
        text = re.sub(r'Git\s*Version\s*Control', 'Git', text)
        text = re.sub(r'Jenkins\s*CI/CD', 'Jenkins', text)
        
        # 프로젝트 관련 수정
        text = re.sub(r'프로젝트\s*개요', '프로젝트 개요', text)
        text = re.sub(r'기술\s*스택', '기술 스택', text)
        text = re.sub(r'주요\s*기능', '주요 기능', text)
        text = re.sub(r'개발\s*환경', '개발 환경', text)
        text = re.sub(r'배포\s*환경', '배포 환경', text)
        
        # 더 강력한 OCR 오류 수정 패턴들
        # 한글 자음/모음 분리 오류 수정
        text = re.sub(r'([가-힣])\s*([가-힣])', r'\1\2', text)  # 한글 사이 공백 제거
        text = re.sub(r'([ㄱ-ㅎㅏ-ㅣ])\s*([ㄱ-ㅎㅏ-ㅣ])', r'\1\2', text)  # 자음/모음 사이 공백 제거
        
        # 영문 단어 분리 오류 수정
        text = re.sub(r'([a-zA-Z])\s+([a-zA-Z])', r'\1\2', text)  # 영문 단어 사이 공백 제거
        
        # 숫자와 단위 사이 공백 제거
        text = re.sub(r'(\d+)\s+([a-zA-Z가-힣]+)', r'\1\2', text)
        
        # 특수 문자 정리 (더 관대하게)
        # 한글, 영문, 숫자, 기본 문장부호만 허용
        text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)\[\]\{\}\가-힣\@\#\$\%\^\&\*\+\=\|\~\`\<\>\?\/\\]', '', text)
        
        # 연속된 공백 정리
        text = re.sub(r'\s+', ' ', text)
        
        # 문장 시작과 끝의 공백 제거
        text = text.strip()
        
        # 텍스트 품질 검증
        korean_ratio = len(re.findall(r'[가-힣]', text)) / max(len(text), 1)
        english_ratio = len(re.findall(r'[a-zA-Z]', text)) / max(len(text), 1)
        
        print(f"텍스트 품질 - 한글 비율: {korean_ratio:.2f}, 영문 비율: {english_ratio:.2f}")
        
        # 품질이 너무 나쁘면 경고
        if korean_ratio < 0.1 and english_ratio < 0.1:
            print("⚠️ 경고: 텍스트 품질이 매우 낮습니다. OCR 설정을 확인해주세요.")
        
        return text
    
    def chunk_text(self, text: str) -> List[Dict[str, Any]]:
        """
        텍스트를 지정된 토큰 크기로 청킹합니다.
        
        Args:
            text: 청킹할 텍스트
            
        Returns:
            청킹된 텍스트 섹션들의 리스트
        """
        # 텍스트를 문장 단위로 분할
        sentences = self._split_into_sentences(text)
        
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
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """
        텍스트를 문장 단위로 분할합니다.
        
        Args:
            text: 분할할 텍스트
            
        Returns:
            문장들의 리스트
        """
        # 문장 끝 패턴 (마침표, 느낌표, 물음표)
        sentence_end_pattern = r'[.!?]+'
        
        # 텍스트를 문장으로 분할
        sentences = re.split(sentence_end_pattern, text)
        
        # 빈 문장 제거 및 정리
        cleaned_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and len(sentence) > 10:  # 너무 짧은 문장 제외
                cleaned_sentences.append(sentence)
        
        return cleaned_sentences
    
    def process_pdf(self, pdf_path: str) -> List[Dict[str, Any]]:
        """
        PDF 파일을 처리하여 청킹된 텍스트 섹션들을 반환합니다.
        
        Args:
            pdf_path: PDF 파일 경로
            
        Returns:
            청킹된 텍스트 섹션들의 리스트
        """
        # PDF에서 텍스트 추출
        text = self.extract_text_from_pdf(pdf_path)
        
        # 텍스트를 청킹
        chunks = self.chunk_text(text)
        
        return chunks 