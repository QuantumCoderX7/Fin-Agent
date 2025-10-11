import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 300000, // 5 minutes timeout
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for logging
api.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error('API Response Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// System endpoints
export const systemAPI = {
  getHealth: () => api.get('/health'),
  getStatus: () => api.get('/status'),
  getStreamingStats: () => api.get('/streaming/stats'),
  cleanupStreams: (maxInactiveSeconds = 300) => 
    api.post('/streaming/cleanup', { max_inactive_seconds: maxInactiveSeconds }),
};

// Research endpoints
export const researchAPI = {
  getStatus: () => api.get('/api/v1/research/'),
  analyze: (data) => api.post('/api/v1/research/analyze', data),
  getTopics: (domain = 'finance') => api.get(`/api/v1/research/topics?domain=${domain}`),
  stream: (data) => api.post('/api/v1/research/stream', data),
};

// Stock endpoints
export const stockAPI = {
  getStatus: () => api.get('/api/v1/stocks/'),
  analyze: (data) => api.post('/api/v1/stocks/analyze', data),
  compare: (data) => api.post('/api/v1/stocks/compare', data),
  getStockInfo: (symbol) => api.get(`/api/v1/stocks/${symbol}/info`),
  getMarketOverview: (sector = null) => 
    api.get(`/api/v1/stocks/market/overview${sector ? `?sector=${sector}` : ''}`),
  getAgentInfo: () => api.get('/api/v1/stocks/info'),
  stream: (data) => api.post('/api/v1/stocks/stream', data),
};

// Evaluation endpoints
export const evaluationAPI = {
  getStatus: () => api.get('/api/v1/evaluation/'),
  assess: (data) => api.post('/api/v1/evaluation/assess', data),
  getMetrics: () => api.get('/api/v1/evaluation/metrics'),
  batchEvaluate: (data) => api.post('/api/v1/evaluation/batch', data),
  stream: (data) => api.post('/api/v1/evaluation/stream', data),
};

// Streaming utilities
export const createEventSource = (url, data = null) => {
  const fullUrl = `${API_BASE_URL}${url}`;
  
  if (data) {
    // For POST requests with data, we need to use fetch with streaming
    return fetch(fullUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream',
      },
      body: JSON.stringify(data),
    });
  } else {
    // For GET requests, use EventSource
    return new EventSource(fullUrl);
  }
};

// Helper function to parse Server-Sent Events
export const parseSSEData = (data) => {
  try {
    return JSON.parse(data);
  } catch (error) {
    return { content: data };
  }
};

export default api;