import apiClient from "./axiosConfig";

export const remediationAPI = {
  /**
   * Gets an AI-generated code fix for a given vulnerability.
   * @param {object} payload
   * @param {string} payload.vulnerableCode The snippet of vulnerable code.
   * @param {string} payload.language The programming language.
   * @param {string} payload.vulnerabilityType A description of the vulnerability.
   * @returns {Promise<object>} An object containing the suggested fix.
   */
  async suggestFix({ vulnerableCode, language, vulnerabilityType }) {
    const response = await apiClient.post("/api/v1/remediate/suggest-fix", {
      vulnerableCode,
      language,
      vulnerabilityType,
    });
    return response.data;
  },
};
