import axios from 'axios';

const BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8080';

export const authAPI = {
  /**
   * Get JWT token after OAuth login
   */
  async getToken() {
    const response = await axios.post(`${BASE_URL}/api/v1/auth/token`, null, {
      withCredentials: true // Include OAuth session cookie
    });
    return response.data;
  },

  /**
   * Get current authenticated user
   */
  async getCurrentUser(token) {
    const response = await axios.get(`${BASE_URL}/api/v1/auth/me`, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });
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
