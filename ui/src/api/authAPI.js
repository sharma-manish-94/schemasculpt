import apiClient, { BASE_URL } from './axiosConfig';
import axios from 'axios';

export const authAPI = {
  /**
   * Get JWT token after OAuth login
   * Note: Uses raw axios for withCredentials to include OAuth session cookie
   */
  async getToken() {
    const response = await axios.post(`${BASE_URL}/api/v1/auth/token`, null, {
      withCredentials: true // Include OAuth session cookie
    });
    return response.data;
  },

  /**
   * Get current authenticated user
   * Uses apiClient which automatically adds token from localStorage
   */
  async getCurrentUser() {
    const response = await apiClient.get('/api/v1/auth/me');
    return response.data;
  },

  /**
   * Logout (clear local state, backend doesn't need to know)
   */
  logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  },

  /**
   * Initiate GitHub OAuth login
   */
  initiateLogin() {
    window.location.href = `${BASE_URL}/oauth2/authorization/github`;
  }
};
