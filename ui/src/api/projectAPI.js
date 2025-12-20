import apiClient from "./axiosConfig";

export const projectAPI = {
  /**
   * Get all projects for the authenticated user
   */
  async getProjects() {
    const response = await apiClient.get("/api/v1/projects");
    return response.data;
  },

  /**
   * Get a specific project
   */
  async getProject(projectId) {
    const response = await apiClient.get(`/api/v1/projects/${projectId}`);
    return response.data;
  },

  /**
   * Create a new project
   */
  async createProject(projectData) {
    const response = await apiClient.post("/api/v1/projects", projectData);
    return response.data;
  },

  /**
   * Update a project
   */
  async updateProject(projectId, updates) {
    const response = await apiClient.put(
      `/api/v1/projects/${projectId}`,
      updates,
    );
    return response.data;
  },

  /**
   * Delete a project
   */
  async deleteProject(projectId) {
    await apiClient.delete(`/api/v1/projects/${projectId}`);
  },

  // Specification Management

  /**
   * Save a new version of the specification
   */
  async saveSpecification(projectId, specData) {
    const response = await apiClient.post(
      `/api/v1/projects/${projectId}/specifications`,
      specData,
    );
    return response.data;
  },

  /**
   * Get the current version of the specification
   */
  async getCurrentSpecification(projectId) {
    const response = await apiClient.get(
      `/api/v1/projects/${projectId}/specifications/current`,
    );
    return response.data;
  },

  /**
   * Get all versions of the specification
   */
  async getSpecificationVersions(projectId) {
    const response = await apiClient.get(
      `/api/v1/projects/${projectId}/specifications`,
    );
    return response.data;
  },

  /**
   * Get a specific version of the specification
   */
  async getSpecificationVersion(projectId, version) {
    const response = await apiClient.get(
      `/api/v1/projects/${projectId}/specifications/versions/${version}`,
    );
    return response.data;
  },

  /**
   * Revert to a previous version
   */
  async revertToVersion(projectId, version, commitMessage) {
    const response = await apiClient.post(
      `/api/v1/projects/${projectId}/specifications/versions/${version}/revert`,
      null,
      { params: { commitMessage } },
    );
    return response.data;
  },
};
