import axios from 'axios';

const BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8080';

const getAuthHeaders = (token) => ({
  headers: {
    Authorization: `Bearer ${token}`
  }
});

export const projectAPI = {
  /**
   * Get all projects for the authenticated user
   */
  async getProjects(token) {
    const response = await axios.get(
      `${BASE_URL}/api/v1/projects`,
      getAuthHeaders(token)
    );
    return response.data;
  },

  /**
   * Get a specific project
   */
  async getProject(token, projectId) {
    const response = await axios.get(
      `${BASE_URL}/api/v1/projects/${projectId}`,
      getAuthHeaders(token)
    );
    return response.data;
  },

  /**
   * Create a new project
   */
  async createProject(token, projectData) {
    const response = await axios.post(
      `${BASE_URL}/api/v1/projects`,
      projectData,
      getAuthHeaders(token)
    );
    return response.data;
  },

  /**
   * Update a project
   */
  async updateProject(token, projectId, updates) {
    const response = await axios.put(
      `${BASE_URL}/api/v1/projects/${projectId}`,
      updates,
      getAuthHeaders(token)
    );
    return response.data;
  },

  /**
   * Delete a project
   */
  async deleteProject(token, projectId) {
    await axios.delete(
      `${BASE_URL}/api/v1/projects/${projectId}`,
      getAuthHeaders(token)
    );
  },

  // Specification Management

  /**
   * Save a new version of the specification
   */
  async saveSpecification(token, projectId, specData) {
    const response = await axios.post(
      `${BASE_URL}/api/v1/projects/${projectId}/specifications`,
      specData,
      getAuthHeaders(token)
    );
    return response.data;
  },

  /**
   * Get the current version of the specification
   */
  async getCurrentSpecification(token, projectId) {
    const response = await axios.get(
      `${BASE_URL}/api/v1/projects/${projectId}/specifications/current`,
      getAuthHeaders(token)
    );
    return response.data;
  },

  /**
   * Get all versions of the specification
   */
  async getSpecificationVersions(token, projectId) {
    const response = await axios.get(
      `${BASE_URL}/api/v1/projects/${projectId}/specifications`,
      getAuthHeaders(token)
    );
    return response.data;
  },

  /**
   * Get a specific version of the specification
   */
  async getSpecificationVersion(token, projectId, version) {
    const response = await axios.get(
      `${BASE_URL}/api/v1/projects/${projectId}/specifications/versions/${version}`,
      getAuthHeaders(token)
    );
    return response.data;
  },

  /**
   * Revert to a previous version
   */
  async revertToVersion(token, projectId, version, commitMessage) {
    const response = await axios.post(
      `${BASE_URL}/api/v1/projects/${projectId}/specifications/versions/${version}/revert`,
      null,
      {
        ...getAuthHeaders(token),
        params: { commitMessage }
      }
    );
    return response.data;
  }
};
