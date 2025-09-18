import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000, // 10초 타임아웃
});

// 요청 인터셉터 - 토큰 자동 추가
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 응답 인터셉터 - 에러 처리
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.reload();
    }
    return Promise.reject(error);
  }
);

export const authAPI = {
  login: async (email: string, password: string) => {
    console.log('로그인 API 호출:', { email, password });
    console.log('API Base URL:', API_BASE_URL);
    
    try {
      const response = await api.post('/auth/login', { email, password });
      console.log('로그인 응답:', response.data);
      return response.data;
    } catch (error) {
      console.error('로그인 API 오류:', error);
      throw error;
    }
  },
  
  register: async (email: string, password: string, role: string = 'USER') => {
    const response = await api.post('/auth/register', { email, password, role });
    return response.data;
  },
  
  verifyToken: async (token: string) => {
    const response = await api.get('/auth/verify', {
      headers: { Authorization: `Bearer ${token}` }
    });
    return response.data;
  }
};

export const policyAPI = {
  upload: async (file: File, company: string, category: string, productType: string, productName: string, securityLevel: string = 'public') => {
    console.log('업로드 시작:', { 
      fileName: file.name, 
      fileSize: file.size, 
      company, 
      category, 
      productType, 
      productName, 
      securityLevel 
    });
    
    const formData = new FormData();
    formData.append('file', file);
    formData.append('company', company);
    formData.append('category', category);
    formData.append('product_type', productType);
    formData.append('product_name', productName);
    formData.append('security_level', securityLevel);
    
    try {
      const response = await api.post('/policies/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 300000  // 5분 타임아웃
      });
      
      console.log('업로드 성공:', response.data);
      return response.data;
    } catch (error: any) {
      console.error('업로드 API 오류:', error);
      console.error('응답 데이터:', error.response?.data);
      console.error('상태 코드:', error.response?.status);
      throw error;
    }
  },
  
  getPolicies: async (skip: number = 0, limit: number = 100) => {
    const response = await api.get(`/policies?skip=${skip}&limit=${limit}`);
    return response.data;
  },
  
  getPolicy: async (policyId: number) => {
    const response = await api.get(`/policies/${policyId}`);
    return response.data;
  },
  
  deletePolicy: async (policyId: number) => {
    const response = await api.delete(`/policies/${policyId}`);
    return response.data;
  },
  
  getPolicyPdf: async (policyId: number) => {
    const response = await api.get(`/policies/${policyId}/pdf`, {
      responseType: 'blob'
    });
    return response;
  },
  
  getPolicyMd: async (policyId: number) => {
    const response = await api.get(`/policies/${policyId}/md`);
    return response;
  }
};

export const searchAPI = {
  search: async (query: string, policyIds?: number[], limit: number = 10, securityLevel: string = 'public') => {
    const response = await api.post('/search', {
      query,
      policy_ids: policyIds,
      limit,
      security_level: securityLevel
    });
    return response.data;
  }
};

export const workflowAPI = {
  getLogs: async (workflowId?: string) => {
    const url = workflowId ? `/workflow/logs?workflow_id=${workflowId}` : '/workflow/logs';
    const response = await api.get(url);
    return response.data;
  }
};

export default api;