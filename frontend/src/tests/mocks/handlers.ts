import { http, HttpResponse } from 'msw';

// Use a wildcard to match requests regardless of the origin (http://localhost:3000 or relative)
const API_BASE = '*/api';

export const handlers = [
  // Auth
  http.get(`${API_BASE}/auth/me`, () => {
    return HttpResponse.json({
      id: 'user-1',
      email: 'test@example.com',
      name: 'Test User',
      avatar_url: 'https://avatar.url',
    });
  }),

  // Documents
  http.get(`${API_BASE}/documents`, () => {
    return HttpResponse.json({
      documents: [
        {
          id: 'doc-1',
          filename: 'test.pdf',
          file_type: 'pdf',
          file_size: 1024,
          status: 'ready',
          created_at: new Date().toISOString(),
        },
        {
          id: 'doc-2',
          filename: 'video.mp4',
          file_type: 'video',
          file_size: 2048,
          status: 'processing',
          created_at: new Date().toISOString(),
        },
      ],
    });
  }),

  http.post(`${API_BASE}/documents/upload`, () => {
    return HttpResponse.json({
      id: 'doc-3',
      filename: 'new.pdf',
      status: 'processing',
    });
  }),

  http.get(`${API_BASE}/documents/:id`, ({ params }) => {
    return HttpResponse.json({
      id: params.id,
      filename: 'test.pdf',
      file_type: 'pdf',
      status: 'ready',
      summary: 'This is a test summary.',
    });
  }),

  http.delete(`${API_BASE}/documents/:id`, () => {
    return new HttpResponse(null, { status: 204 });
  }),

  // Chat
  http.post(`${API_BASE}/chat/sessions`, () => {
    return HttpResponse.json({
      id: 'session-1',
      title: 'New Session',
    });
  }),

  http.get(`${API_BASE}/chat/sessions/:id/messages`, () => {
    return HttpResponse.json([
      { id: 'msg-1', role: 'user', content: 'Hello' },
      { id: 'msg-2', role: 'assistant', content: 'Hi there!' },
    ]);
  }),
];
