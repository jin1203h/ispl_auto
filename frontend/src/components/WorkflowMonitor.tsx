import React, { useState, useEffect } from 'react';
import { CheckCircle, XCircle, AlertCircle, RefreshCw, Clock, FileText, Activity } from 'lucide-react';

interface WorkflowLog {
  log_id: number;
  workflow_id: string;
  step_name: string;
  status: string;
  input_data?: any;
  output_data?: any;
  error_message?: string;
  execution_time?: number;
  created_at: string;
}


interface WorkflowMonitorProps {
  isAuthenticated: boolean;
}

const WorkflowMonitor: React.FC<WorkflowMonitorProps> = ({ isAuthenticated }) => {
  const [logs, setLogs] = useState<WorkflowLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedWorkflow, setSelectedWorkflow] = useState<string>('');
  const [workflowIds, setWorkflowIds] = useState<string[]>([]);

  useEffect(() => {
    if (isAuthenticated) {
      loadWorkflowLogs();
      loadWorkflowIds();
    }
  }, [isAuthenticated]);


  const loadWorkflowLogs = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      console.log('워크플로우 로그 로드 시도, 토큰:', token ? '존재' : '없음');
      
      const response = await fetch('/workflow/logs', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      console.log('워크플로우 로그 응답 상태:', response.status);
      
      if (response.ok) {
        const data = await response.json() as WorkflowLog[];
        setLogs(data);
        console.log('워크플로우 로그 로드 성공:', data.length, '개');
      } else {
        console.error('워크플로우 로그 로드 실패:', response.status, response.statusText);
        const errorText = await response.text();
        console.error('오류 내용:', errorText);
      }
    } catch (error) {
      console.error('워크플로우 로그 로드 실패:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadWorkflowIds = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/workflow/logs', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      if (response.ok) {
        const data = await response.json() as WorkflowLog[];
        const uniqueIds = [...new Set(data.map((log: WorkflowLog) => log.workflow_id))];
        setWorkflowIds(uniqueIds);
      }
    } catch (error) {
      console.error('워크플로우 ID 로드 실패:', error);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'error':
        return <XCircle className="w-4 h-4 text-red-500" />;
      case 'running':
        return <Clock className="w-4 h-4 text-blue-500" />;
      default:
        return <AlertCircle className="w-4 h-4 text-yellow-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'error':
        return 'bg-red-100 text-red-800';
      case 'running':
        return 'bg-blue-100 text-blue-800';
      default:
        return 'bg-yellow-100 text-yellow-800';
    }
  };

  const filteredLogs = selectedWorkflow 
    ? logs.filter(log => log.workflow_id === selectedWorkflow)
    : logs;

  if (!isAuthenticated) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <Activity className="w-16 h-16 mx-auto mb-4 text-gray-400" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">로그인이 필요합니다</h2>
          <p className="text-gray-600">워크플로우 모니터링을 보려면 로그인해주세요.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      <div className="flex-shrink-0 p-6 border-b border-gray-200">
        <div className="flex justify-between items-center">
          <h2 className="text-2xl font-bold text-gray-900">워크플로우 모니터링</h2>
          <div className="flex gap-4">
          <select
            value={selectedWorkflow}
            onChange={(e) => setSelectedWorkflow(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900 bg-white"
          >
            <option value="" className="text-gray-900">모든 워크플로우</option>
            {workflowIds.map(id => (
              <option key={id} value={id} className="text-gray-900">{id}</option>
            ))}
          </select>
          <button
            onClick={loadWorkflowLogs}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            새로고침
          </button>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-hidden">
        {loading ? (
          <div className="flex justify-center items-center h-full">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
          </div>
        ) : (
          <div className="h-full bg-white rounded-lg shadow overflow-hidden">
            <div className="h-full overflow-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50 sticky top-0 z-10">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    워크플로우 ID
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    단계
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    상태
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    실행 시간
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    생성 시간
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    상세 정보
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredLogs.map((log) => (
                  <tr key={log.log_id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-900">
                      {log.workflow_id}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {log.step_name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center gap-2">
                        {getStatusIcon(log.status)}
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(log.status)}`}>
                          {log.status}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {log.execution_time ? `${log.execution_time}ms` : '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {new Date(log.created_at).toLocaleString('ko-KR')}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900">
                      <div className="space-y-2 max-w-xs">
                        {log.input_data && (
                          <div className="bg-blue-50 border border-blue-200 rounded p-2">
                            <span className="text-xs font-medium text-blue-800">입력:</span>
                            <pre className="text-xs text-blue-700 mt-1 whitespace-pre-wrap break-words max-h-24 overflow-y-auto">
                              {JSON.stringify(log.input_data, null, 2)}
                            </pre>
                          </div>
                        )}
                        {log.output_data && (
                          <div className="bg-green-50 border border-green-200 rounded p-2">
                            <span className="text-xs font-medium text-green-800">출력:</span>
                            <pre className="text-xs text-green-700 mt-1 whitespace-pre-wrap break-words max-h-24 overflow-y-auto">
                              {JSON.stringify(log.output_data, null, 2)}
                            </pre>
                          </div>
                        )}
                        {log.error_message && (
                          <div className="bg-red-50 border border-red-200 rounded p-2">
                            <span className="text-xs font-medium text-red-800">오류:</span>
                            <p className="text-xs text-red-700 mt-1 whitespace-pre-wrap break-words max-h-24 overflow-y-auto">{log.error_message}</p>
                          </div>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          
            {filteredLogs.length === 0 && (
              <div className="flex items-center justify-center h-full">
                <div className="text-center">
                  <FileText className="mx-auto h-12 w-12 text-gray-400" />
                  <h3 className="mt-2 text-sm font-medium text-gray-900">워크플로우 로그가 없습니다</h3>
                  <p className="mt-1 text-sm text-gray-500">
                    {selectedWorkflow ? '선택한 워크플로우에 대한 로그가 없습니다.' : '아직 실행된 워크플로우가 없습니다.'}
                  </p>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default WorkflowMonitor;