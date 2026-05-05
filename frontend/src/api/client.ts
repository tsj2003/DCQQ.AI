/**
 * API client for communicating with the DocQA AI backend.
 */

import axios from 'axios';

// Use relative paths in production/docker, or VITE_API_URL if provided
const API_BASE_URL = import.meta.env.VITE_API_URL || (typeof window !== 'undefined' ? window.location.origin : '');

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Attach JWT token to every request
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 responses
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// --- Auth API ---
export const authApi = {
  getGoogleAuthUrl: () => `${API_BASE_URL}/api/auth/google`,
  getMe: () => apiClient.get('/api/auth/me'),
  googleCallback: (code: string) => apiClient.get(`/api/auth/google/callback?code=${code}`),
  refreshToken: () => apiClient.post('/api/auth/refresh'),
  guestLogin: () => apiClient.post('/api/auth/guest'),
};

// --- Documents API ---
export const documentsApi = {
  upload: (file: File, onProgress?: (progress: number) => void) => {
    const formData = new FormData();
    formData.append('file', file);
    return apiClient.post('/api/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (event) => {
        if (event.total && onProgress) {
          onProgress(Math.round((event.loaded * 100) / event.total));
        }
      },
    });
  },
  list: () => apiClient.get('/api/documents'),
  get: (id: string) => apiClient.get(`/api/documents/${id}`),
  delete: (id: string) => apiClient.delete(`/api/documents/${id}`),
  getSummary: (id: string) => apiClient.get(`/api/documents/${id}/summary`),
  regenerateSummary: (id: string) => apiClient.post(`/api/documents/${id}/summary`),
};

// --- Chat API ---
export const chatApi = {
  createSession: (documentId: string, title?: string) =>
    apiClient.post('/api/chat/sessions', { document_id: documentId, title }),
  listSessions: () => apiClient.get('/api/chat/sessions'),
  getHistory: (sessionId: string) =>
    apiClient.get(`/api/chat/sessions/${sessionId}/messages`),

  // Streaming chat via SSE
  sendMessageStream: async function* (sessionId: string, content: string) {
    const token = localStorage.getItem('access_token');
    const response = await fetch(`${API_BASE_URL}/api/chat/sessions/${sessionId}/messages`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ content }),
    });

    if (!response.ok) {
      throw new Error(`Chat request failed: ${response.status}`);
    }

    const reader = response.body?.getReader();
    if (!reader) throw new Error('No response body');

    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6));
            yield data;
          } catch {
            // Skip malformed JSON
          }
        }
      }
    }
  },
};

// --- Media API ---
export const mediaApi = {
  getMediaUrl: (documentId: string) => {
    const token = localStorage.getItem('access_token');
    return `${API_BASE_URL}/api/media/${documentId}?token=${token}`;
  },
  getTranscript: (documentId: string) =>
    apiClient.get(`/api/media/${documentId}/transcript`),
};

export default apiClient;
