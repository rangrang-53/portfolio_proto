import React, { useState } from 'react';
import { askQuestion, QuestionResponse } from '../services/api';

interface Message {
  id: string;
  text: string;
  isUser: boolean;
  timestamp: Date;
  sources?: Array<{
    chunk_id: string;
    snippet: string;
  }>;
}

interface ChatInterfaceProps {
  onAskQuestion: (question: string) => Promise<QuestionResponse>;
  isReady: boolean;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ onAskQuestion, isReady }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!inputValue.trim() || isLoading || !isReady) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      text: inputValue,
      isUser: true,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      const response = await onAskQuestion(inputValue);
      
      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: response.answer,
        isUser: false,
        timestamp: new Date(),
        sources: response.source,
      };

      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: error instanceof Error ? error.message : '오류가 발생했습니다.',
        isUser: false,
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('ko-KR', {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="flex flex-col h-full">
      {/* 메시지 영역 */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {!isReady && (
          <div className="flex justify-center items-center h-full">
            <div className="text-center text-gray-500">
              <div className="text-lg font-medium mb-2">PDF를 먼저 업로드해주세요</div>
              <div className="text-sm">PDF 파일을 업로드하면 질문할 수 있습니다</div>
            </div>
          </div>
        )}
        
        {isReady && messages.length === 0 && (
          <div className="flex justify-center items-center h-full">
            <div className="text-center text-gray-500">
              <div className="text-lg font-medium mb-2">질문을 입력하세요</div>
              <div className="text-sm">PDF 내용에 대해 질문해보세요</div>
            </div>
          </div>
        )}

        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.isUser ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                message.isUser
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-200 text-gray-800'
              }`}
            >
              <div className="text-sm">{message.text}</div>
              <div className="text-xs opacity-70 mt-1">
                {formatTime(message.timestamp)}
              </div>
              
              {/* 소스 정보 표시 */}
              {!message.isUser && message.sources && message.sources.length > 0 && (
                <div className="mt-3 pt-2 border-t border-gray-300">
                  <div className="text-xs font-semibold mb-2">
                    참고 소스 ({message.sources.length}개)
                  </div>
                  {message.sources.map((source, index) => (
                    <div key={source.chunk_id} className="text-xs mb-2">
                      <div className="font-medium">
                        소스 {index + 1} (ID: {source.chunk_id})
                      </div>
                      <div className="text-gray-600 mt-1">
                        {source.snippet}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
        
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-gray-200 text-gray-800 max-w-xs lg:max-w-md px-4 py-2 rounded-lg">
              <div className="text-sm">답변을 생성하고 있습니다...</div>
            </div>
          </div>
        )}
      </div>

      {/* 입력 영역 */}
      <form onSubmit={handleSubmit} className="p-4 border-t border-gray-200">
        <div className="flex space-x-2">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder={isReady ? "질문을 입력하세요..." : "PDF를 먼저 업로드해주세요"}
            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 disabled:text-gray-500"
            disabled={isLoading || !isReady}
          />
          <button
            type="submit"
            disabled={isLoading || !inputValue.trim() || !isReady}
            className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            전송
          </button>
        </div>
      </form>
    </div>
  );
};

export default ChatInterface; 