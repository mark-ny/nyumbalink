import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

const api = axios.create({
  baseURL: API_URL,
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
});

// Request interceptor – attach JWT
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) config.headers.Authorization = `Bearer ${token}`;
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor – handle 401 / token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true;
      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (!refreshToken) throw new Error('No refresh token');

        const res = await axios.post(`${API_URL}/auth/refresh`, {}, {
          headers: { Authorization: `Bearer ${refreshToken}` },
        });
        const { access_token } = res.data;
        localStorage.setItem('access_token', access_token);
        original.headers.Authorization = `Bearer ${access_token}`;
        return api(original);
      } catch {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

// ── Auth ──────────────────────────────────────────────────────────────
export const authAPI = {
  register: (data) => api.post('/auth/register', data),
  login: (data) => api.post('/auth/login', data),
  me: () => api.get('/auth/me'),
  updateMe: (data) => api.put('/auth/me', data),
  changePassword: (data) => api.post('/auth/change-password', data),
  logout: () => api.post('/auth/logout'),
};

// ── Properties ────────────────────────────────────────────────────────
export const propertiesAPI = {
  list: (params) => api.get('/properties', { params }),
  get: (id) => api.get(`/properties/${id}`),
  create: (data) => api.post('/properties', data),
  update: (id, data) => api.put(`/properties/${id}`, data),
  delete: (id) => api.delete(`/properties/${id}`),
  uploadImages: (id, formData) => api.post(`/properties/${id}/images`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  deleteImage: (propertyId, imageId) => api.delete(`/properties/${propertyId}/images/${imageId}`),
  myListings: (params) => api.get('/properties/my/listings', { params }),
  saved: () => api.get('/properties/saved'),
  save: (id) => api.post(`/properties/${id}/save`),
};

// ── Search ────────────────────────────────────────────────────────────
export const searchAPI = {
  search: (params) => api.get('/search', { params }),
};

// ── Inquiries ─────────────────────────────────────────────────────────
export const inquiriesAPI = {
  create: (data) => api.post('/inquiries', data),
  myInquiries: (params) => api.get('/inquiries/my', { params }),
  byProperty: (propertyId, params) => api.get(`/inquiries/property/${propertyId}`, { params }),
};

// ── Viewings ──────────────────────────────────────────────────────────
export const viewingsAPI = {
  create: (data) => api.post('/viewings', data),
  my: (params) => api.get('/viewings/my', { params }),
  updateStatus: (id, data) => api.put(`/viewings/${id}/status`, data),
};

// ── Payments ──────────────────────────────────────────────────────────
export const paymentsAPI = {
  initiate: (data) => api.post('/payments/initiate', data),
  status: (id) => api.get(`/payments/status/${id}`),
  query: (checkoutId) => api.get(`/payments/query/${checkoutId}`),
  my: () => api.get('/payments/my'),
};

// ── Admin ─────────────────────────────────────────────────────────────
export const adminAPI = {
  dashboard: () => api.get('/admin/dashboard'),
  properties: (params) => api.get('/admin/properties', { params }),
  verifyProperty: (id, data) => api.put(`/admin/properties/${id}/verify`, data),
  featureProperty: (id) => api.put(`/admin/properties/${id}/feature`),
  users: (params) => api.get('/admin/users', { params }),
  toggleUserActive: (id) => api.put(`/admin/users/${id}/toggle-active`),
  updateUserRole: (id, data) => api.put(`/admin/users/${id}/role`, data),
  leads: (params) => api.get('/admin/leads', { params }),
  payments: (params) => api.get('/admin/payments', { params }),
};

// ── Notifications ─────────────────────────────────────────────────────
export const notificationsAPI = {
  list: (params) => api.get('/notifications', { params }),
  markRead: (id) => api.put(`/notifications/${id}/read`),
  markAllRead: () => api.put('/notifications/read-all'),
};

export default api;
