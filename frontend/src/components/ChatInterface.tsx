import React, { useState, useRef, useEffect } from 'react';
import { Send, Upload, FileText, Search } from 'lucide-react';
import { searchAPI } from '../services/api';

interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  searchResults?: SearchResult[];
}

interface SearchResult {
  policy_id: number;
  policy_name: string;
  company: string;
  relevance_score: number;
  matched_text: string;
  page_number?: number;
}

interface ChatInterfaceProps {
  isAuthenticated: boolean;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ isAuthenticated = false }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: inputMessage,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      // 검색 API 호출
      const response = await searchAPI.search(inputMessage, undefined, 10, 'public');
      
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: response.answer || '검색 결과를 찾을 수 없습니다.',
        timestamp: new Date(),
        searchResults: response.results || [],
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('검색 오류:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: '죄송합니다. 검색 중 오류가 발생했습니다.',
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setUploadedFile(file);
    }
  };

  const clearChat = () => {
    setMessages([]);
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('ko-KR', { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  return (
    <div className="h-full flex flex-col bg-gray-900">
      {/* 헤더 */}
      <div className="flex-shrink-0 p-6 border-b border-gray-700 bg-gray-800">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-white">AI 채팅</h2>
            <p className="text-gray-400 mt-1">보험약관에 대해 질문하고 답변을 받아보세요</p>
          </div>
          <button
            onClick={clearChat}
            className="px-4 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-600 transition-colors"
          >
            대화 초기화
          </button>
        </div>
      </div>

      {/* 메시지 영역 */}
      <div className="flex-1 overflow-hidden">
        <div className="h-full overflow-y-auto p-6 space-y-4">
        {messages.length === 0 ? (
          <div className="text-center text-gray-400 mt-8">
            <Search className="w-16 h-16 mx-auto mb-4 opacity-50" />
            <p className="text-lg">안녕하세요! 보험약관에 대해 질문해주세요</p>
            <p className="text-sm mt-2">예: "보험금 지급 조건은 무엇인가요?"</p>
          </div>
        ) : (
          messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-3xl px-4 py-3 rounded-lg ${
                  message.type === 'user'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-700 text-gray-100'
                }`}
              >
                <div className="whitespace-pre-wrap">{message.content}</div>
                <div className="text-xs opacity-70 mt-2">
                  {formatTime(message.timestamp)}
                </div>
                
                {/* 검색 결과 표시 */}
                {message.searchResults && message.searchResults.length > 0 && (
                  <div className="mt-4 space-y-2">
                    <div className="text-sm font-semibold mb-2">관련 약관:</div>
                    {message.searchResults.map((result, index) => (
                      <div
                        key={index}
                        className="bg-gray-600 rounded p-3 text-sm"
                      >
                        <div className="font-medium text-blue-300 mb-1">
                          {result.policy_name} ({result.company})
                        </div>
                        <div className="text-gray-300 text-xs mb-2">
                          관련도: {(result.relevance_score * 100).toFixed(1)}%
                        </div>
                        <div className="text-gray-200 text-xs">
                          {result.matched_text}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))
        )}
        
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-gray-700 text-gray-100 px-4 py-3 rounded-lg">
              <div className="flex items-center gap-2">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                <span>검색 중...</span>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
        </div>
      </div>

      {/* 입력 영역 */}
      <div className="flex-shrink-0 p-6 border-t border-gray-700 bg-gray-800">
        <div className="max-w-4xl mx-auto">
          {/* 파일 업로드 */}
          <div className="mb-4">
            <label className="flex items-center gap-2 text-gray-400 text-sm cursor-pointer">
              <Upload className="w-4 h-4" />
              <span>파일 업로드</span>
              <input
                type="file"
                accept=".pdf"
                onChange={handleFileUpload}
                className="hidden"
              />
            </label>
            {uploadedFile && (
              <div className="mt-2 flex items-center gap-2 text-sm text-gray-300">
                <FileText className="w-4 h-4" />
                <span>{uploadedFile.name}</span>
                <button
                  onClick={() => setUploadedFile(null)}
                  className="text-red-400 hover:text-red-300"
                >
                  ×
                </button>
              </div>
            )}
          </div>

          {/* 메시지 입력 */}
          <div className="flex gap-4">
            <div className="flex-1 relative">
              <textarea
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="보험약관에 대해 질문해주세요..."
                className="w-full px-4 py-3 bg-gray-700 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                rows={3}
                disabled={isLoading}
              />
            </div>
            <button
              onClick={handleSendMessage}
              disabled={!inputMessage.trim() || isLoading}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              <Send className="w-4 h-4" />
              전송
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;
