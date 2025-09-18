import React, { useState } from 'react';
import { Image as ImageIcon, Search, FileText, Eye, Loader2 } from 'lucide-react';

interface ImageAnalysisProps {
  isAuthenticated: boolean;
}

interface AnalysisResult {
  success: boolean;
  workflow_id: string;
  query: string;
  image_path: string;
  extracted_text: string;
  image_description: string;
  search_results: Array<{
    policy_id: number;
    policy_name: string;
    relevance_score: number;
    matched_text: string;
    source: string;
  }>;
  final_response: string;
  error_message?: string;
}

const ImageAnalysis: React.FC<ImageAnalysisProps> = ({ isAuthenticated }) => {
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [query, setQuery] = useState('');
  const [analyzing, setAnalyzing] = useState(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      // 이미지 파일 타입 확인
      if (!file.type.startsWith('image/')) {
        setError('이미지 파일만 업로드 가능합니다.');
        return;
      }
      
      // 파일 크기 확인 (10MB 제한)
      if (file.size > 10 * 1024 * 1024) {
        setError('파일 크기는 10MB 이하여야 합니다.');
        return;
      }
      
      setSelectedImage(file);
      setError(null);
      setResult(null);
      
      // 이미지 미리보기 생성
      const reader = new FileReader();
      reader.onload = (e) => {
        setImagePreview(e.target?.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleAnalyze = async () => {
    if (!selectedImage || !query.trim()) {
      setError('이미지와 질문을 모두 입력해주세요.');
      return;
    }

    try {
      setAnalyzing(true);
      setError(null);

      const formData = new FormData();
      formData.append('image', selectedImage);
      formData.append('query', query);

      const token = localStorage.getItem('token');
      const response = await fetch('/image/analyze', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData,
      });

      if (response.ok) {
        const data = await response.json();
        console.log('이미지 분석 결과:', data);
        setResult(data);
      } else {
        const errorData = await response.json();
        console.error('이미지 분석 오류:', errorData);
        setError(errorData.detail || `이미지 분석에 실패했습니다. (${response.status})`);
      }
    } catch (err: any) {
      setError(`이미지 분석 오류: ${err.message}`);
    } finally {
      setAnalyzing(false);
    }
  };

  const resetForm = () => {
    setSelectedImage(null);
    setImagePreview(null);
    setQuery('');
    setResult(null);
    setError(null);
    // 파일 입력 초기화
    const fileInput = document.getElementById('image-upload') as HTMLInputElement;
    if (fileInput) fileInput.value = '';
  };

  if (!isAuthenticated) {
    return (
      <div className="p-6">
        <div className="text-center py-12">
          <ImageIcon className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">로그인이 필요합니다</h3>
          <p className="mt-1 text-sm text-gray-500">
            이미지 분석 기능을 사용하려면 로그인해주세요.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      <div className="flex-shrink-0 p-6 border-b border-gray-200">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">이미지 분석</h2>
        <p className="text-gray-600">
          이미지를 업로드하고 질문을 입력하면, AI가 이미지를 분석하고 관련 보험약관을 찾아드립니다.
        </p>
      </div>
      
      <div className="flex-1 overflow-hidden">
        <div className="h-full overflow-y-auto p-6">
          <div className="max-w-4xl mx-auto">

        {/* 업로드 섹션 */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <div className="space-y-4">
            {/* 이미지 업로드 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                이미지 업로드
              </label>
              <div className="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-md hover:border-gray-400 transition-colors">
                <div className="space-y-1 text-center">
                  <ImageIcon className="mx-auto h-12 w-12 text-gray-400" />
                  <div className="flex text-sm text-gray-600">
                    <label
                      htmlFor="image-upload"
                      className="relative cursor-pointer bg-white rounded-md font-medium text-blue-600 hover:text-blue-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-blue-500"
                    >
                      <span>이미지 선택</span>
                      <input
                        id="image-upload"
                        name="image-upload"
                        type="file"
                        className="sr-only"
                        accept="image/*"
                        onChange={handleImageSelect}
                      />
                    </label>
                    <p className="pl-1">또는 드래그 앤 드롭</p>
                  </div>
                  <p className="text-xs text-gray-500">PNG, JPG, JPEG (최대 10MB)</p>
                </div>
              </div>
              {selectedImage && (
                <div className="mt-2">
                  <div className="flex items-center gap-2 mb-2">
                    <FileText className="w-4 h-4 text-green-500" />
                    <span className="text-sm text-gray-600">{selectedImage.name}</span>
                    <span className="text-xs text-gray-500">
                      ({(selectedImage.size / 1024 / 1024).toFixed(2)} MB)
                    </span>
                  </div>
                  {imagePreview && (
                    <div className="mt-2">
                      <div className="bg-gray-100 p-2 rounded-md">
                        <img 
                          src={imagePreview} 
                          alt="미리보기" 
                          className="max-w-full h-48 object-contain border border-gray-300 rounded-md bg-white"
                          style={{ filter: 'contrast(1.2) brightness(1.1)' }}
                        />
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* 질문 입력 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                분석할 내용에 대한 질문
              </label>
              <textarea
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="예: 이 이미지에서 보험금 지급 조건은 무엇인가요?"
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 text-gray-900 placeholder-gray-500"
                rows={3}
              />
            </div>

            {/* 버튼들 */}
            <div className="flex gap-3">
              <button
                onClick={handleAnalyze}
                disabled={!selectedImage || !query.trim() || analyzing}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {analyzing ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Search className="w-4 h-4" />
                )}
                {analyzing ? '분석 중...' : '이미지 분석'}
              </button>
              
              <button
                onClick={resetForm}
                className="px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400"
              >
                초기화
              </button>
            </div>
          </div>
        </div>

        {/* 오류 메시지 */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-md p-4 mb-6">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">오류</h3>
                <div className="mt-2 text-sm text-red-700">{error}</div>
              </div>
            </div>
          </div>
        )}

        {/* 분석 결과 */}
        {result && (
          <div className="space-y-6 max-h-96 overflow-y-auto">
            {/* 워크플로우 정보 */}
            <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
              <div className="flex items-center gap-2">
                <Eye className="w-5 h-5 text-blue-600" />
                <h3 className="text-sm font-medium text-blue-800">분석 완료</h3>
              </div>
              <p className="mt-1 text-sm text-blue-700">
                워크플로우 ID: {result.workflow_id}
              </p>
            </div>

            {/* 추출된 텍스트 */}
            {result.extracted_text && (
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">추출된 텍스트</h3>
                <div className="bg-gray-900 rounded-md p-4">
                  <pre className="whitespace-pre-wrap text-sm text-green-400 font-mono">
                    {result.extracted_text}
                  </pre>
                </div>
              </div>
            )}

            {/* 이미지 설명 */}
            {result.image_description && (
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">이미지 분석 결과</h3>
                <div className="prose max-w-none">
                  <p className="text-gray-700">{result.image_description}</p>
                </div>
              </div>
            )}

            {/* 관련 정책 */}
            {result.search_results && result.search_results.length > 0 && (
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">관련 정책 정보</h3>
                <div className="space-y-3">
                  {result.search_results.map((policy, index) => (
                    <div key={index} className="border border-gray-200 rounded-md p-4">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="font-medium text-gray-900">{policy.policy_name}</h4>
                        <span className="text-sm text-blue-600">
                          관련도: {(policy.relevance_score * 100).toFixed(1)}%
                        </span>
                      </div>
                      <p className="text-sm text-gray-600">{policy.matched_text}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 최종 응답 */}
            {result.final_response && (
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">종합 분석 결과</h3>
                <div className="prose max-w-none">
                  <div className="whitespace-pre-wrap text-gray-700">
                    {result.final_response}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ImageAnalysis;
