import axios from 'axios';
import { useAuthStore } from '../stores/authStore';

const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      const refreshToken = useAuthStore.getState().refreshToken;
      if (refreshToken) {
        try {
          const res = await axios.post('/api/auth/token/refresh', {
            refresh_token: refreshToken,
          });
          const { access_token, refresh_token } = res.data.data;
          useAuthStore.getState().setTokens(access_token, refresh_token);
          error.config.headers.Authorization = `Bearer ${access_token}`;
          return axios(error.config);
        } catch {
          useAuthStore.getState().logout();
        }
      }
    }
    return Promise.reject(error);
  }
);

export default api;

export const authService = {
  register: (data: { email: string; password: string; full_name?: string }) =>
    api.post('/auth/register', data),
  login: (data: { email: string; password: string }) =>
    api.post('/auth/login', data),
  getMe: () => api.get('/auth/me'),
};

export const gymService = {
  register: (data: { name: string; address?: string; phone?: string; email?: string }) =>
    api.post('/gyms/register', data),
  getMine: () => api.get('/gyms/me'),
  get: (id: number) => api.get(`/gyms/${id}`),
  update: (id: number, data: Record<string, string>) => api.put(`/gyms/${id}`, data),
  getPhoneNumbers: (id: number) => api.get(`/gyms/${id}/phone-numbers`),
  setEvolutionCredentials: (id: number, data: { api_key: string; instance_name: string }) =>
    api.post(`/gyms/${id}/evolution-credentials`, data),
  connectWhatsApp: (id: number, data: { phone_number: string }) =>
    api.post(`/gyms/${id}/whatsapp/connect`, data),
  getWhatsAppStatus: (id: number) => api.get(`/gyms/${id}/whatsapp/status`),
  sendOnboardingWelcome: (id: number, data: { phone_number: string; owner_name?: string }) =>
    api.post(`/gyms/${id}/whatsapp/send-onboarding-welcome`, data),
};

export const memberService = {
  list: (gymId: number) => api.get(`/gyms/${gymId}/members`),
  create: (data: {
    gym_id: number;
    name: string;
    phone_number: string;
    email?: string;
    schedule?: string;
    weekly_schedule?: Array<{ day: string; start_time: string; end_time: string; activity: string }>;
  }) =>
    api.post('/members', data),
  update: (id: number, data: {
    name?: string;
    phone_number?: string;
    email?: string;
    status?: string;
    schedule?: string;
    weekly_schedule?: Array<{ day: string; start_time: string; end_time: string; activity: string }>;
  }) =>
    api.put(`/members/${id}`, data),
  delete: (id: number) => api.delete(`/members/${id}`),
  listPayments: (id: number) => api.get(`/members/${id}/payments`),
  createPayment: (
    id: number,
    data: {
      amount: number;
      currency?: string;
      payment_method?: string;
      status?: string;
      note?: string;
      paid_at?: string;
    }
  ) => api.post(`/members/${id}/payments`, data),
};

export const notificationService = {
  getTemplates: (gymId: number) => api.get(`/gyms/${gymId}/templates`),
  createTemplate: (data: { gym_id: number; name: string; content: string }) =>
    api.post('/templates', data),
  getScheduled: () => api.get('/notifications/scheduled'),
  schedule: (data: Record<string, unknown>) => api.post('/notifications/schedule', data),
};

export const analyticsService = {
  getKPIs: (gymId: number) => api.get(`/analytics/kpis?gym_id=${gymId}`),
  getMessageVolume: (gymId: number) => api.get(`/analytics/message-volume?gym_id=${gymId}`),
  getMessageLogs: (gymId: number) => api.get(`/logs/messages?gym_id=${gymId}`),
};

export const aiService = {
  getRuntimeConfig: () => api.get('/ai/runtime-config'),
};
