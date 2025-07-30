import React, { useState, useRef } from 'react';
import { Upload, FileText, X, CheckCircle, AlertCircle, Info } from 'lucide-react';
import { uploadPDF } from '../services/api';

interface PDFUploadProps {
  onUploadSuccess: () => void;
}

const PDFUpload: React.FC<PDFUploadProps> = ({ onUploadSuccess }) => {
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [message, setMessage] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = event.target.files?.[0];
    if (selectedFile && selectedFile.type === 'application/pdf') {
      setFile(selectedFile);
      setUploadStatus('idle');
      setMessage('');
    } else {
      setMessage('PDF 파일만 업로드할 수 있습니다.');
      setUploadStatus('error');
    }
  };

  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    const droppedFile = event.dataTransfer.files[0];
    if (droppedFile && droppedFile.type === 'application/pdf') {
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
    if (!file) return;

    setIsUploading(true);
    setUploadStatus('idle');
    setMessage('');

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
    }
  };

  const removeFile = () => {
    setFile(null);
    setUploadStatus('idle');
    setMessage('');
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto">
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
          <FileText className="w-6 h-6 mr-2 text-primary-600" />
          PDF 문서 업로드
        </h2>

        <div
          className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
            file
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
          />

          {!file ? (
            <div>
              <Upload className="w-12 h-12 mx-auto text-gray-400 mb-4" />
              <p className="text-lg font-medium text-gray-700 mb-2">
                PDF 파일을 드래그하거나 클릭하여 업로드
              </p>
              <p className="text-sm text-gray-500 mb-4">
                또는 <span className="text-primary-600">여기를 클릭</span>하여 파일 선택
              </p>
              <button
                onClick={() => fileInputRef.current?.click()}
                className="bg-primary-600 text-white px-6 py-2 rounded-lg hover:bg-primary-700 transition-colors"
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
                  className="ml-4 p-1 text-gray-400 hover:text-red-500 transition-colors"
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
                disabled={isUploading}
                className={`px-6 py-2 rounded-lg text-white font-medium transition-colors ${
                  isUploading
                    ? 'bg-gray-400 cursor-not-allowed'
                    : 'bg-primary-600 hover:bg-primary-700'
                }`}
              >
                {isUploading ? '업로드 중... (OCR 처리 중일 수 있습니다)' : '업로드'}
              </button>
            </div>
          )}
        </div>

        <div className="mt-4 text-sm text-gray-600">
          <p>• PDF 파일만 지원됩니다</p>
          <p>• 최대 파일 크기: 10MB</p>
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
  );
};

export default PDFUpload; 