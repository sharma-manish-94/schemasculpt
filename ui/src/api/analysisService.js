/**
 * Advanced Analysis Service
 * Handles API calls for advanced architectural analyzers:
 * - Taint Analysis
 * - Authorization Matrix
 * - Schema Similarity
 * - Zombie API Detection
 */

import axios from "axios";

const API_BASE_URL = process.env.REACT_APP_API_URL || "http://localhost:8080";
const AI_SERVICE_URL =
  process.env.REACT_APP_AI_SERVICE_URL || "http://localhost:8000";

/**
 * Run Taint Analysis - Track sensitive data flow
 * @param {string} sessionId - Session ID
 * @returns {Promise<Object>} Taint analysis results
 */
export const runTaintAnalysis = async (sessionId) => {
  try {
    const response = await axios.get(
      `${API_BASE_URL}/api/v1/sessions/${sessionId}/analysis/taint-analysis`,
      {
        timeout: 30000,
      },
    );

    return {
      success: true,
      data: response.data,
    };
  } catch (error) {
    console.error("Taint analysis failed:", error);
    return {
      success: false,
      error: error.response?.data?.message || error.message,
    };
  }
};

/**
 * Get AI interpretation of taint analysis results
 * @param {Object} taintResults - Raw taint analysis results
 * @param {string} specText - OpenAPI specification
 * @returns {Promise<Object>} AI interpretation
 */
export const interpretTaintAnalysis = async (taintResults, specText) => {
  try {
    const response = await axios.post(
      `${AI_SERVICE_URL}/ai/analyze/taint-analysis`,
      {
        vulnerabilities: taintResults.vulnerabilities || [],
        spec_text: specText,
      },
      {
        timeout: 60000,
      },
    );

    return {
      success: true,
      interpretation: response.data,
    };
  } catch (error) {
    console.error("Taint analysis interpretation failed:", error);
    return {
      success: false,
      error: error.response?.data?.detail?.message || error.message,
    };
  }
};

/**
 * Run Authorization Matrix Analysis
 * @param {string} sessionId - Session ID
 * @returns {Promise<Object>} Authorization matrix results
 */
export const runAuthzMatrixAnalysis = async (sessionId) => {
  try {
    const response = await axios.get(
      `${API_BASE_URL}/api/v1/sessions/${sessionId}/analysis/authz-matrix`,
      {
        timeout: 30000,
      },
    );

    return {
      success: true,
      data: response.data,
    };
  } catch (error) {
    console.error("Authz matrix analysis failed:", error);
    return {
      success: false,
      error: error.response?.data?.message || error.message,
    };
  }
};

/**
 * Get AI interpretation of authorization matrix results
 * @param {Object} authzResults - Raw authz matrix results
 * @param {string} specText - OpenAPI specification
 * @returns {Promise<Object>} AI interpretation
 */
export const interpretAuthzMatrix = async (authzResults, specText) => {
  try {
    const response = await axios.post(
      `${AI_SERVICE_URL}/ai/analyze/authz-matrix`,
      {
        scopes: authzResults.scopes || [],
        matrix: authzResults.matrix || {},
        spec_text: specText,
      },
      {
        timeout: 60000,
      },
    );

    return {
      success: true,
      interpretation: response.data,
    };
  } catch (error) {
    console.error("Authz matrix interpretation failed:", error);
    return {
      success: false,
      error: error.response?.data?.detail?.message || error.message,
    };
  }
};

/**
 * Run Schema Similarity Analysis
 * @param {string} sessionId - Session ID
 * @returns {Promise<Object>} Schema similarity results
 */
export const runSchemaSimilarityAnalysis = async (sessionId) => {
  try {
    const response = await axios.get(
      `${API_BASE_URL}/api/v1/sessions/${sessionId}/analysis/schema-similarity`,
      {
        timeout: 30000,
      },
    );

    return {
      success: true,
      data: response.data,
    };
  } catch (error) {
    console.error("Schema similarity analysis failed:", error);
    return {
      success: false,
      error: error.response?.data?.message || error.message,
    };
  }
};

/**
 * Get AI interpretation of schema similarity results
 * @param {Object} similarityResults - Raw similarity results
 * @param {string} specText - OpenAPI specification
 * @returns {Promise<Object>} AI interpretation
 */
export const interpretSchemaSimilarity = async (
  similarityResults,
  specText,
) => {
  try {
    const response = await axios.post(
      `${AI_SERVICE_URL}/ai/analyze/schema-similarity`,
      {
        clusters: similarityResults.clusters || [],
        spec_text: specText,
      },
      {
        timeout: 60000,
      },
    );

    return {
      success: true,
      interpretation: response.data,
    };
  } catch (error) {
    console.error("Schema similarity interpretation failed:", error);
    return {
      success: false,
      error: error.response?.data?.detail?.message || error.message,
    };
  }
};

/**
 * Run Zombie API Detection
 * @param {string} sessionId - Session ID
 * @returns {Promise<Object>} Zombie API detection results
 */
export const runZombieApiDetection = async (sessionId) => {
  try {
    const response = await axios.get(
      `${API_BASE_URL}/api/v1/sessions/${sessionId}/analysis/zombie-apis`,
      {
        timeout: 30000,
      },
    );

    return {
      success: true,
      data: response.data,
    };
  } catch (error) {
    console.error("Zombie API detection failed:", error);
    return {
      success: false,
      error: error.response?.data?.message || error.message,
    };
  }
};

/**
 * Get AI interpretation of zombie API detection results
 * @param {Object} zombieResults - Raw zombie API results
 * @param {string} specText - OpenAPI specification
 * @returns {Promise<Object>} AI interpretation
 */
export const interpretZombieApis = async (zombieResults, specText) => {
  try {
    const response = await axios.post(
      `${AI_SERVICE_URL}/ai/analyze/zombie-apis`,
      {
        shadowedEndpoints: zombieResults.shadowedEndpoints || [],
        orphanedOperations: zombieResults.orphanedOperations || [],
        spec_text: specText,
      },
      {
        timeout: 60000,
      },
    );

    return {
      success: true,
      interpretation: response.data,
    };
  } catch (error) {
    console.error("Zombie API interpretation failed:", error);
    return {
      success: false,
      error: error.response?.data?.detail?.message || error.message,
    };
  }
};

/**
 * Run comprehensive architectural analysis (all 4 analyzers)
 * @param {string} sessionId - Session ID
 * @param {string} specText - OpenAPI specification
 * @returns {Promise<Object>} Comprehensive analysis results
 */
export const runComprehensiveAnalysis = async (sessionId, specText) => {
  try {
    // Run all 4 analyzers in parallel
    const [taintRes, authzRes, similarityRes, zombieRes] = await Promise.all([
      runTaintAnalysis(sessionId),
      runAuthzMatrixAnalysis(sessionId),
      runSchemaSimilarityAnalysis(sessionId),
      runZombieApiDetection(sessionId),
    ]);

    // Check if any failed
    if (
      !taintRes.success ||
      !authzRes.success ||
      !similarityRes.success ||
      !zombieRes.success
    ) {
      return {
        success: false,
        error: "One or more analyzers failed",
      };
    }

    // Get comprehensive AI interpretation
    const response = await axios.post(
      `${AI_SERVICE_URL}/ai/analyze/comprehensive-architecture`,
      {
        taint_analysis: taintRes.data,
        authz_matrix: authzRes.data,
        schema_similarity: similarityRes.data,
        zombie_apis: zombieRes.data,
        spec_text: specText,
      },
      {
        timeout: 120000, // 2 minutes for comprehensive analysis
      },
    );

    return {
      success: true,
      raw_results: {
        taint: taintRes.data,
        authz: authzRes.data,
        similarity: similarityRes.data,
        zombie: zombieRes.data,
      },
      interpretation: response.data,
    };
  } catch (error) {
    console.error("Comprehensive analysis failed:", error);
    return {
      success: false,
      error: error.response?.data?.detail?.message || error.message,
    };
  }
};
