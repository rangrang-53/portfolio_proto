export interface Source {
  chunk_id: string;
  snippet: string;
}

export interface QAResponse {
  answer: string;
  source: Source[];
}

export interface UploadResponse {
  message: string;
  success: boolean;
}

export interface ChatMessage {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  sources?: Source[];
}

export interface SystemStatus {
  isConnected: boolean;
  message: string;
} 