import api from './api';

export const authService = {
  async register(username, email, password) {
    const response = await api.post('/auth/register', {
      username,
      email,
      password,
    });
    if (response.data && response.data.token) {
      localStorage.setItem('stego_auth_token', response.data.token);
      localStorage.setItem('stego_user_data', JSON.stringify(response.data));
    }
    return response.data;
  },

  async login(email, password) {
    const response = await api.post('/auth/login', {
      email,
      password,
    });
    if (response.data && response.data.token) {
      localStorage.setItem('stego_auth_token', response.data.token);
      localStorage.setItem('stego_user_data', JSON.stringify(response.data));
    }
    return response.data;
  },

  async getProfile() {
    const response = await api.get('/auth/profile');
    return response.data;
  },

  logout() {
    localStorage.removeItem('stego_auth_token');
    localStorage.removeItem('stego_user_data');
  },

  getCurrentUser() {
    const data = localStorage.getItem('stego_user_data');
    return data ? JSON.parse(data) : null;
  },

  getToken() {
    return localStorage.getItem('stego_auth_token');
  },
};
