import React, { useState } from 'react';
import PDFUpload from './components/PDFUpload';
import ChatInterface from './components/ChatInterface';
import SystemStatus from './components/SystemStatus';
import { askQuestion, QuestionResponse } from './services/api';

function App() {
  const [isReady, setIsReady] = useState(false);

  const handleAskQuestion = async (question: string): Promise<QuestionResponse> => {
    return await askQuestion(question);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-6xl mx-auto">
          {/* 헤더 */}
          <div className="text-center mb-8">
            <h1 className="text-4xl font-bold text-gray-900 mb-2">
              PDF Q&A 시스템
            </h1>
            <p className="text-lg text-gray-600">
              PDF 문서를 업로드하고 질문하세요
            </p>
          </div>

          {/* 시스템 상태 */}
          <div className="mb-6">
            <SystemStatus />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* PDF 업로드 */}
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">
                PDF 업로드
              </h2>
              <PDFUpload 
                onUploadSuccess={() => setIsReady(true)}
              />
            </div>

            {/* 채팅 인터페이스 */}
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">
                질문하기
              </h2>
              <div className="h-96">
                <ChatInterface 
                  onAskQuestion={handleAskQuestion} 
                  isReady={isReady}
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App; 