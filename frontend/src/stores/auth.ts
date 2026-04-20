import { create } from 'zustand';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

interface User {
  id: number;
  username: string;
  created_at: string;
}

interface AuthState {
  token: string | null;
  user: User | null;
  isAuthenticated: boolean;
}

interface AuthActions {
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  checkAuth: () => Promise<void>;
}

interface AuthStore extends AuthState, AuthActions {}

export const useAuthStore = create<AuthStore>((set) => ({
  token: localStorage.getItem('token') || null,
  user: null,
  isAuthenticated: false,

  login: async (username, password) => {
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({ detail: '登录失败' }));
      throw new Error(err.detail || '登录失败');
    }

    const loginData = await response.json();
    const token = loginData.access_token;
    localStorage.setItem('token', token);

    const meResponse = await fetch(`${API_BASE_URL}/api/v1/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!meResponse.ok) {
      localStorage.removeItem('token');
      throw new Error('登录状态校验失败');
    }
    const meData = await meResponse.json();
    set({ token, user: meData, isAuthenticated: true });
  },

  logout: () => {
    localStorage.removeItem('token');
    set({ token: null, user: null, isAuthenticated: false });
  },

  checkAuth: async () => {
    const token = localStorage.getItem('token');
    if (!token) {
      set({ token: null, user: null, isAuthenticated: false });
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/auth/me`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) {
        localStorage.removeItem('token');
        set({ token: null, user: null, isAuthenticated: false });
        return;
      }
      const user = await response.json();
      set({ token, user, isAuthenticated: true });
    } catch {
      localStorage.removeItem('token');
      set({ token: null, user: null, isAuthenticated: false });
    }
  },
}));
