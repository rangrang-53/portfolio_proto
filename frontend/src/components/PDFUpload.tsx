import React, { useState, useRef, useEffect } from 'react';
import { Upload, FileText, X, CheckCircle, AlertCircle, Info, Loader2 } from 'lucide-react';
import { uploadPDF, getProcessingStatus } from '../services/api';

interface PDFUploadProps {
  onUploadSuccess: () => void;
  isEnabled: boolean;
}

const PDFUpload: React.FC<PDFUploadProps> = ({ onUploadSuccess, isEnabled }) => {
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [message, setMessage] = useState('');
  const [progress, setProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState('');
  const [currentPage, setCurrentPage] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const progressIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // 진행상황 추적
  useEffect(() => {
    if (isUploading) {
      const checkProgress = async () => {
        try {
          const status = await getProcessingStatus();
          setProgress(status.progress);
          setCurrentStep(status.current_step);
          setCurrentPage(status.current_page);
          setTotalPages(status.total_pages);
          
          // 처리 완료 시 인터벌 정리
          if (!status.is_processing) {
            if (progressIntervalRef.current) {
              clearInterval(progressIntervalRef.current);
              progressIntervalRef.current = null;
            }
          }
        } catch (error) {
          console.error('진행상황 조회 오류:', error);
        }
      };

      // 1초마다 진행상황 조회
      progressIntervalRef.current = setInterval(checkProgress, 1000);
      
      // 컴포넌트 언마운트 시 인터벌 정리
      return () => {
        if (progressIntervalRef.current) {
          clearInterval(progressIntervalRef.current);
        }
      };
    }
  }, [isUploading]);

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (!isEnabled) return;
    
    const selectedFile = event.target.files?.[0];
    if (selectedFile && selectedFile.type === 'application/pdf') {
      // 파일 크기 제한 (100MB)
      const maxSize = 100 * 1024 * 1024; // 100MB
      if (selectedFile.size > maxSize) {
        setMessage('파일 크기가 100MB를 초과합니다. 더 작은 파일을 선택해주세요.');
        setUploadStatus('error');
        return;
      }
      setFile(selectedFile);
      setUploadStatus('idle');
      setMessage('');
    } else {
      setMessage('PDF 파일만 업로드할 수 있습니다.');
      setUploadStatus('error');
    }
  };

  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    if (!isEnabled) return;
    
    event.preventDefault();
    const droppedFile = event.dataTransfer.files[0];
    if (droppedFile && droppedFile.type === 'application/pdf') {
      // 파일 크기 제한 (100MB)
      const maxSize = 100 * 1024 * 1024; // 100MB
      if (droppedFile.size > maxSize) {
        setMessage('파일 크기가 100MB를 초과합니다. 더 작은 파일을 선택해주세요.');
        setUploadStatus('error');
        return;
      }
      setFile(droppedFile);
      setUploadStatus('idle');
      setMessage('');
    } else {
      setMessage('PDF 파일만 업로드할 수 있습니다.');
      setUploadStatus('error');
    }
  };

  const handleDragOver = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
  };

  const handleUpload = async () => {
    if (!file || !isEnabled) return;

    setIsUploading(true);
    setUploadStatus('idle');
    setMessage('');
    setProgress(0);
    setCurrentStep('');
    setCurrentPage(0);
    setTotalPages(0);

    try {
      const response = await uploadPDF(file);
      setUploadStatus('success');
      setMessage(response.message);
      onUploadSuccess();
    } catch (error) {
      setUploadStatus('error');
      setMessage(error instanceof Error ? error.message : '업로드에 실패했습니다.');
    } finally {
      setIsUploading(false);
      if (progressIntervalRef.current) {
        clearInterval(progressIntervalRef.current);
        progressIntervalRef.current = null;
      }
    }
  };

  const removeFile = () => {
    setFile(null);
    setUploadStatus('idle');
    setMessage('');
    setProgress(0);
    setCurrentStep('');
    setCurrentPage(0);
    setTotalPages(0);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // 진행상황 메시지 생성
  const getProgressMessage = () => {
    if (progress >= 80) {
      return "거의 다 됐습니다! 🎉";
    } else if (progress >= 60) {
      return "분석이 진행 중입니다...";
    } else if (progress >= 30) {
      return "OCR 처리가 진행 중입니다...";
    } else {
      return "PDF 파일을 분석하고 있습니다...";
    }
  };

  return (
    <>
      {/* 업로드 중 모달 */}
      {isUploading && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-8 flex flex-col items-center shadow-xl max-w-md w-full mx-4">
            <Loader2 className="w-12 h-12 text-primary-600 animate-spin mb-4" />
            <h3 className="text-xl font-semibold text-gray-900 mb-2">OCR 추출 중</h3>
            
            {/* 진행상황 표시 */}
            <div className="w-full mb-4">
              <div className="flex justify-between text-sm text-gray-600 mb-2">
                <span>{currentStep}</span>
                <span>{progress}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-primary-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${progress}%` }}
                ></div>
              </div>
            </div>
            
            {/* 페이지 정보 */}
            {totalPages > 0 && (
              <div className="text-sm text-gray-600 mb-4">
                페이지 {currentPage} / {totalPages}
              </div>
            )}
            
            <p className="text-gray-600 text-center">
              {getProgressMessage()}
            </p>
          </div>
        </div>
      )}

      <div className="w-full max-w-2xl mx-auto">
        <div className={`bg-white rounded-lg shadow-lg p-6 ${!isEnabled ? 'opacity-50' : ''}`}>
          <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
            <FileText className="w-6 h-6 mr-2 text-primary-600" />
            PDF 문서 업로드
          </h2>

          {!isEnabled && (
            <div className="mb-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <div className="flex items-center text-blue-800">
                <CheckCircle className="w-5 h-5 mr-2" />
                <span className="font-medium">PDF가 이미 업로드되었습니다</span>
              </div>
              <p className="text-sm text-blue-700 mt-1">
                다른 PDF를 분석하려면 '다른 PDF 분석하기' 버튼을 클릭하세요.
              </p>
            </div>
          )}

          <div
            className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
              !isEnabled
                ? 'border-gray-200 bg-gray-50 cursor-not-allowed'
                : file
                ? 'border-green-300 bg-green-50'
                : 'border-gray-300 hover:border-primary-400'
            }`}
            onDrop={handleDrop}
            onDragOver={handleDragOver}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf"
              onChange={handleFileSelect}
              className="hidden"
              disabled={!isEnabled}
            />

            {!file ? (
              <div>
                <Upload className={`w-12 h-12 mx-auto mb-4 ${!isEnabled ? 'text-gray-300' : 'text-gray-400'}`} />
                <p className={`text-lg font-medium mb-2 ${!isEnabled ? 'text-gray-400' : 'text-gray-700'}`}>
                  {!isEnabled ? 'PDF 업로드가 비활성화되었습니다' : 'PDF 파일을 드래그하거나 클릭하여 업로드'}
                </p>
                <p className={`text-sm mb-4 ${!isEnabled ? 'text-gray-400' : 'text-gray-500'}`}>
                  {!isEnabled ? '다른 PDF 분석하기 버튼을 클릭하여 활성화하세요' : '또는 여기를 클릭하여 파일 선택'}
                </p>
                <button
                  onClick={() => fileInputRef.current?.click()}
                  disabled={!isEnabled}
                  className={`px-6 py-2 rounded-lg font-medium transition-colors ${
                    !isEnabled
                      ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                      : 'bg-primary-600 text-white hover:bg-primary-700'
                  }`}
                >
                  파일 선택
                </button>
              </div>
            ) : (
              <div>
                <div className="flex items-center justify-center mb-4">
                  <FileText className="w-8 h-8 text-green-600 mr-3" />
                  <div className="text-left">
                    <p className="font-medium text-gray-900">{file.name}</p>
                    <p className="text-sm text-gray-500">
                      {(file.size / 1024 / 1024).toFixed(2)} MB
                    </p>
                  </div>
                  <button
                    onClick={removeFile}
                    disabled={!isEnabled}
                    className={`ml-4 p-1 transition-colors ${
                      !isEnabled
                        ? 'text-gray-300 cursor-not-allowed'
                        : 'text-gray-400 hover:text-red-500'
                    }`}
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>

                {uploadStatus === 'success' && (
                  <div className="flex items-center justify-center text-green-600 mb-4">
                    <CheckCircle className="w-5 h-5 mr-2" />
                    <span className="font-medium">{message}</span>
                  </div>
                )}

                {uploadStatus === 'error' && (
                  <div className="flex items-center justify-center text-red-600 mb-4">
                    <AlertCircle className="w-5 h-5 mr-2" />
                    <span className="font-medium">{message}</span>
                  </div>
                )}

                <button
                  onClick={handleUpload}
                  disabled={isUploading || !isEnabled}
                  className={`px-6 py-2 rounded-lg text-white font-medium transition-colors ${
                    isUploading || !isEnabled
                      ? 'bg-gray-400 cursor-not-allowed'
                      : 'bg-primary-600 hover:bg-primary-700'
                  }`}
                >
                  업로드
                </button>
              </div>
            )}
          </div>

          <div className="mt-4 text-sm text-gray-600">
            <p>• PDF 파일만 지원됩니다</p>
            <p>• 최대 파일 크기: 100MB</p>
            <p>• 업로드된 문서는 벡터 데이터베이스에 저장됩니다</p>
            <div className="mt-3 p-3 bg-blue-50 rounded-lg border border-blue-200">
              <div className="flex items-start">
                <Info className="w-4 h-4 text-blue-600 mr-2 mt-0.5 flex-shrink-0" />
                <div>
                  <p className="font-medium text-blue-800 mb-1">OCR 기능 지원</p>
                  <p className="text-blue-700 text-xs">
                    스캔된 PDF나 이미지 기반 PDF도 처리할 수 있습니다. 
                    Tesseract OCR이 설치되어 있어야 합니다.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default PDFUpload; 