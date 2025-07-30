import React, { useState, useEffect } from 'react';
import { Wifi, WifiOff, AlertCircle, CheckCircle, Database } from 'lucide-react';
import { getSystemStatus, SystemStatus as SystemStatusType } from '../services/api';

const SystemStatus: React.FC = () => {
  const [isConnected, setIsConnected] = useState<boolean | null>(null);
  const [systemStatus, setSystemStatus] = useState<SystemStatusType | null>(null);
  const [isChecking, setIsChecking] = useState(true);

  useEffect(() => {
    const checkStatus = async () => {
      try {
        const status = await getSystemStatus();
        setSystemStatus(status);
        setIsConnected(true);
      } catch (error) {
        setIsConnected(false);
        setSystemStatus(null);
      } finally {
        setIsChecking(false);
      }
    };

    checkStatus();

    // 30초마다 상태 확인
    const interval = setInterval(checkStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  if (isChecking) {
    return (
      <div className="flex items-center space-x-2 text-gray-500">
        <div className="w-4 h-4 border-2 border-gray-300 border-t-blue-600 rounded-full animate-spin"></div>
        <span className="text-sm">시스템 상태 확인 중...</span>
      </div>
    );
  }

  return (
    <div className="flex items-center justify-between bg-white rounded-lg shadow-sm p-4">
      <div className="flex items-center space-x-4">
        {/* 서버 연결 상태 */}
        <div className="flex items-center space-x-2">
          {isConnected ? (
            <>
              <CheckCircle className="w-4 h-4 text-green-600" />
              <span className="text-sm text-green-600 font-medium">서버 연결됨</span>
            </>
          ) : (
            <>
              <AlertCircle className="w-4 h-4 text-red-600" />
              <span className="text-sm text-red-600 font-medium">서버 연결 안됨</span>
            </>
          )}
        </div>

        {/* 벡터 데이터베이스 상태 */}
        {systemStatus && (
          <div className="flex items-center space-x-2">
            <Database className="w-4 h-4 text-blue-600" />
            <span className="text-sm text-gray-600">
              벡터: {systemStatus.vector_count}개
            </span>
          </div>
        )}
      </div>

      {/* 시스템 정보 */}
      {systemStatus && (
        <div className="text-xs text-gray-500">
          차원: {systemStatus.index_dimension} | 
          사용률: {Math.round(systemStatus.index_fullness * 100)}%
        </div>
      )}
    </div>
  );
};

export default SystemStatus; 