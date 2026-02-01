import apiClient from "./axiosConfig";

export const implementationAPI = {
  /**
   * Gets the implementation source code for a given operationId.
   * @param {number} projectId The ID of the project.
   * @param {string} operationId The operationId to look up.
   * @returns {Promise<object>} An object containing the implementation details.
   */
  async getImplementation(projectId, operationId) {
    const response = await apiClient.get(
      `/api/v1/implementations/projects/${projectId}/operations`,
      {
        params: { operationId },
      },
    );
    return response.data;
  },
};
