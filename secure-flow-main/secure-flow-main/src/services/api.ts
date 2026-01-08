import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor to add session token if available
api.interceptors.request.use((config) => {
  const token = sessionStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export interface LoginCredentials {
  username: string;
  password?: string; // Optional if using biocreds later, but typically required
}

export interface AuthResponse {
  session_id: string;
  token: string;
  trust_score: number;
}

export interface KeystrokeData {
  [key: string]: any; // Define strict types based on backend expectation later
}

export interface VoiceVerificationResponse {
  verified: boolean;
  trust_score: number;
}

export const authApi = {
  login: async (credentials: LoginCredentials): Promise<AuthResponse> => {
    const response = await api.post('/auth/login', credentials);
    return response.data;
  },

  sendKeystrokeData: async (data: KeystrokeData[]): Promise<void> => {
    await api.post('/auth/keystroke', data);
  },

  getRiskScore: async (): Promise<{
    risk_level: string;
    trust_score: number | null;
    keystroke_score?: number | null;
    voice_score?: number | null;
    behavioral_score?: number | null;
  }> => {
    const response = await api.get('/auth/risk');
    return response.data;
  },

  verifyVoice: async (audioBlob: Blob): Promise<VoiceVerificationResponse> => {
    const formData = new FormData();
    formData.append('audio', audioBlob);
    const response = await api.post('/auth/voice/verify', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
};

export default api;
