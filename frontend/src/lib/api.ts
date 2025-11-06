import axios from 'axios';
import { AuthResponse } from '@/types';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;

// Auth API
export const authAPI = {
  login: (username: string, password: string) =>
    api.post<AuthResponse>('/auth/login', { username, password }),

  register: (data: any) =>
    api.post<AuthResponse>('/auth/register', data),

  getCurrentUser: () =>
    api.get('/auth/me'),
};

// Exam API
export const examAPI = {
  list: () => api.get('/exams'),

  get: (id: number) => api.get(`/exams/${id}`),

  create: (data: any) => api.post('/exams', data),

  update: (id: number, data: any) => api.put(`/exams/${id}`, data),

  delete: (id: number) => api.delete(`/exams/${id}`),

  enroll: (examId: number, studentIds: number[]) =>
    api.post(`/exams/${examId}/enroll`, { student_ids: studentIds }),
};

// Session API
export const sessionAPI = {
  start: (examId: number) =>
    api.post('/sessions/start', { exam_id: examId }),

  get: (sessionId: number) =>
    api.get(`/sessions/${sessionId}`),

  getEvents: (sessionId: number) =>
    api.get(`/sessions/${sessionId}/events`),

  getBehaviorReport: (sessionId: number) =>
    api.get(`/sessions/${sessionId}/behavior-report`),
};

// Submission API
export const submissionAPI = {
  submit: (sessionId: number, answers: Array<{ question_id: number; answer_text: string }>) =>
    api.post('/submissions', { session_id: sessionId, answers }),

  get: (submissionId: number) =>
    api.get(`/submissions/${submissionId}`),
};

// Admin API
export const adminAPI = {
  listStudents: () => api.get('/admin/students'),

  getExamSessions: (examId: number) =>
    api.get(`/admin/exams/${examId}/sessions`),

  getLiveSessions: () => api.get('/admin/live-sessions'),
};
