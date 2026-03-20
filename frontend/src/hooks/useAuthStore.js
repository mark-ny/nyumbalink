import { create } from 'zustand';
import { authAPI } from '../services/api';

const useAuthStore = create((set, get) => ({
  user: JSON.parse(localStorage.getItem('user') || 'null'),
  accessToken: localStorage.getItem('access_token'),
  isAuthenticated: !!localStorage.getItem('access_token'),
  isLoading: false,

  login: async (credentials) => {
    set({ isLoading: true });
    try {
      const res = await authAPI.login(credentials);
      const { user, access_token, refresh_token } = res.data;
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('refresh_token', refresh_token);
      localStorage.setItem('user', JSON.stringify(user));
      set({ user, accessToken: access_token, isAuthenticated: true, isLoading: false });
      return { success: true, user };
    } catch (err) {
      set({ isLoading: false });
      return { success: false, error: err.response?.data?.error || 'Login failed' };
    }
  },

  register: async (data) => {
    set({ isLoading: true });
    try {
      const res = await authAPI.register(data);
      const { user, access_token, refresh_token } = res.data;
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('refresh_token', refresh_token);
      localStorage.setItem('user', JSON.stringify(user));
      set({ user, accessToken: access_token, isAuthenticated: true, isLoading: false });
      return { success: true, user };
    } catch (err) {
      set({ isLoading: false });
      return { success: false, error: err.response?.data?.error || 'Registration failed' };
    }
  },

  logout: async () => {
    try { await authAPI.logout(); } catch {}
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    set({ user: null, accessToken: null, isAuthenticated: false });
  },

  refreshUser: async () => {
    try {
      const res = await authAPI.me();
      const user = res.data.user;
      localStorage.setItem('user', JSON.stringify(user));
      set({ user });
    } catch {}
  },

  updateUser: (updates) => {
    const updated = { ...get().user, ...updates };
    localStorage.setItem('user', JSON.stringify(updated));
    set({ user: updated });
  },

  isAdmin: () => get().user?.role === 'admin',
  isOwner: () => ['owner', 'admin', 'agent'].includes(get().user?.role),
}));

export default useAuthStore;
