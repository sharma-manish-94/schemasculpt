import axios from "axios";
import { API_CONFIG, REQUEST_CONFIG } from "../config/constants";
import { ERROR_TYPES } from "../store/types";

// Configure axios defaults
axios.defaults.timeout = REQUEST_CONFIG.DEFAULT_TIMEOUT;

const handleApiError = (error, fallbackMessage) => {
    console.error(fallbackMessage, error);

    if (error.code === 'ECONNABORTED') {
        return {
            success: false,
            error: 'Request timeout - please try again',
            type: ERROR_TYPES.TIMEOUT_ERROR
        };
    }

    if (error.response) {
        return {
            success: false,
            error: error.response.data?.detail || error.response.data?.message || fallbackMessage,
            type: ERROR_TYPES.SERVER_ERROR,
            statusCode: error.response.status
        };
    }

    if (error.request) {
        return {
            success: false,
            error: 'Unable to connect to server',
            type: ERROR_TYPES.NETWORK_ERROR
        };
    }

    return {
        success: false,
        error: error.message || fallbackMessage,
        type: ERROR_TYPES.NETWORK_ERROR
    };
};



export const validateSpec = async (sessionId) => {
    if (!sessionId) {
        return {
            success: false,
            error: "Session ID is required",
            type: ERROR_TYPES.VALIDATION_ERROR
        };
    }

    try {
        const response = await axios.post(
            `${API_CONFIG.BASE_URL}/sessions/${sessionId}/spec/validate`
        );
        return {
            success: true,
            data: response.data,
        };
    } catch (error) {
        return handleApiError(error, "Validation failed");
    }
};

export const applyQuickFix = async (sessionId, fixRequest) => {
    if (!sessionId || !fixRequest) {
        return {
            success: false,
            error: "Session ID and fix request are required",
            type: ERROR_TYPES.VALIDATION_ERROR
        };
    }

    try {
        const url = `${API_CONFIG.BASE_URL}/sessions/${sessionId}/spec/fix`;
        const response = await axios.post(url, fixRequest);
        return {
            success: true,
            data: response.data
        };
    } catch (error) {
        return handleApiError(error, "Failed to apply fix");
    }
};

export const updateOperation = async (sessionId, updateRequest) => {
    if (!sessionId || !updateRequest) {
        return {
            success: false,
            error: "Session ID and update request are required",
            type: ERROR_TYPES.VALIDATION_ERROR
        };
    }

    try {
        const response = await axios.patch(
            `${API_CONFIG.BASE_URL}/sessions/${sessionId}/spec/operations`,
            updateRequest
        );
        return {
            success: true,
            data: response.data,
        };
    } catch (error) {
        return handleApiError(error, "Failed to update operation");
    }
};

export const updateSessionSpec = async (sessionId, specText) => {
    if (!sessionId || !specText) {
        return {
            success: false,
            error: "Session ID and spec text are required",
            type: ERROR_TYPES.VALIDATION_ERROR
        };
    }

    try {
        await axios.put(`${API_CONFIG.BASE_URL}/sessions/${sessionId}/spec`, {
            specText: specText
        }, {
            headers: { 'Content-Type': 'application/json' }
        });
        return { success: true };
    } catch (error) {
        return handleApiError(error, "Failed to update session spec");
    }
};

export const getSessionSpec = async (sessionId) => {
    if (!sessionId) {
        return {
            success: false,
            error: "Session ID is required",
            type: ERROR_TYPES.VALIDATION_ERROR
        };
    }

    try {
        const response = await axios.get(
            `${API_CONFIG.BASE_URL}/sessions/${sessionId}/spec`
        );
        return {
            success: true,
            data: response.data,
        };
    } catch (error) {
        return handleApiError(error, "Failed to fetch latest spec");
    }
};

export const getOperationDetails = async (sessionId, path, method) => {
    if (!sessionId || !path || !method) {
        return {
            success: false,
            error: "Session ID, path, and method are required",
            type: ERROR_TYPES.VALIDATION_ERROR
        };
    }

    try {
        const response = await axios.get(
            `${API_CONFIG.BASE_URL}/sessions/${sessionId}/spec/operations`,
            {
                params: { path, method }
            }
        );
        return {
            success: true,
            data: response.data,
        };
    } catch (error) {
        return handleApiError(error, "Failed to fetch operation details");
    }
};

export const executeAiAction = async (sessionId, prompt) => {
    if (!sessionId || !prompt) {
        return {
            success: false,
            error: "Session ID and prompt are required",
            type: ERROR_TYPES.VALIDATION_ERROR
        };
    }

    try {
        const url = `${API_CONFIG.BASE_URL}/sessions/${sessionId}/spec/transform`;
        const response = await axios.post(url, {prompt});
        return {
            success: true,
            data: response.data
        };
    } catch (error) {
        return {
            success: false,
            error: error.message || 'AI processing failed',
            updatedSpecText: `Error: Could not connect to the AI service.\n\nDetails:\n${error.message}`,
        };
    }
};

export const startMockServer = async (specText) => {
    if (!specText) {
        return {
            success: false,
            error: "Spec text is required",
            type: ERROR_TYPES.VALIDATION_ERROR
        };
    }

    try {
        const response = await axios.post(
            `${API_CONFIG.BASE_URL}/sessions/mock`,
            specText,
            {
                headers: { "Content-Type": "text/plain" },
            }
        );
        return { success: true, data: response.data };
    } catch (error) {
        return handleApiError(error, "Failed to start mock server");
    }
};

export const executeProxyRequest = async (requestDetails) => {
    if (!requestDetails) {
        return {
            success: false,
            error: "Request details are required",
            type: ERROR_TYPES.VALIDATION_ERROR
        };
    }

    try {
        const response = await axios.post(
            `${API_CONFIG.BASE_URL}/proxy/request`,
            requestDetails
        );
        return { success: true, data: response.data };
    } catch (error) {
        const errorResponse = error.response?.data || {
            statusCode: 500,
            body: `Could not connect to the server. Details: ${error.message}`,
        };
        return { success: false, error: errorResponse };
    }
};

export const refreshMockSpec = async (mockId, specText) => {
    if (!mockId || !specText) {
        return {
            success: false,
            error: "Mock ID and spec text are required",
            type: ERROR_TYPES.VALIDATION_ERROR
        };
    }

    try {
        const response = await axios.put(
            `${API_CONFIG.BASE_URL}/sessions/${mockId}/spec`,
            { specText },
            {
                headers: { "Content-Type": "application/json" },
            }
        );
        return { success: true, data: response.data };
    } catch (error) {
        return handleApiError(error, "Failed to refresh mock spec");
    }
};

export const explainValidationIssue = async (explanationRequest, sessionId = null) => {
    if (!explanationRequest) {
        return {
            success: false,
            error: "Explanation request is required",
            type: ERROR_TYPES.VALIDATION_ERROR
        };
    }

    try {
        const params = sessionId ? { sessionId } : {};
        const response = await axios.post(
            `${API_CONFIG.BASE_URL}/explanations/explain`,
            explanationRequest,
            { params }
        );
        return {
            success: true,
            data: response.data,
        };
    } catch (error) {
        return handleApiError(error, "Failed to get explanation");
    }
};

// API Hardening Services
export const hardenOperation = async (sessionId, hardenRequest) => {
    if (!sessionId || !hardenRequest) {
        return {
            success: false,
            error: "Session ID and harden request are required",
            type: ERROR_TYPES.VALIDATION_ERROR
        };
    }

    try {
        const response = await axios.post(
            `${API_CONFIG.BASE_URL}/sessions/${sessionId}/hardening/operations`,
            hardenRequest
        );
        return {
            success: true,
            data: response.data,
        };
    } catch (error) {
        return handleApiError(error, "Failed to harden operation");
    }
};

export const addOAuth2Security = async (sessionId, path, method) => {
    if (!sessionId || !path || !method) {
        return {
            success: false,
            error: "Session ID, path, and method are required",
            type: ERROR_TYPES.VALIDATION_ERROR
        };
    }

    try {
        const response = await axios.post(
            `${API_CONFIG.BASE_URL}/sessions/${sessionId}/hardening/operations/oauth2`,
            { path, method }
        );
        return {
            success: true,
            data: response.data,
        };
    } catch (error) {
        return handleApiError(error, "Failed to add OAuth2 security");
    }
};

export const addRateLimiting = async (sessionId, path, method, policy = "100/hour") => {
    if (!sessionId || !path || !method) {
        return {
            success: false,
            error: "Session ID, path, and method are required",
            type: ERROR_TYPES.VALIDATION_ERROR
        };
    }

    try {
        const response = await axios.post(
            `${API_CONFIG.BASE_URL}/sessions/${sessionId}/hardening/operations/rate-limiting`,
            { path, method, policy }
        );
        return {
            success: true,
            data: response.data,
        };
    } catch (error) {
        return handleApiError(error, "Failed to add rate limiting");
    }
};

export const addCaching = async (sessionId, path, method, ttl = "300") => {
    if (!sessionId || !path || !method) {
        return {
            success: false,
            error: "Session ID, path, and method are required",
            type: ERROR_TYPES.VALIDATION_ERROR
        };
    }

    try {
        const response = await axios.post(
            `${API_CONFIG.BASE_URL}/sessions/${sessionId}/hardening/operations/caching`,
            { path, method, ttl }
        );
        return {
            success: true,
            data: response.data,
        };
    } catch (error) {
        return handleApiError(error, "Failed to add caching");
    }
};

export const hardenOperationComplete = async (sessionId, path, method) => {
    if (!sessionId || !path || !method) {
        return {
            success: false,
            error: "Session ID, path, and method are required",
            type: ERROR_TYPES.VALIDATION_ERROR
        };
    }

    try {
        const response = await axios.post(
            `${API_CONFIG.BASE_URL}/sessions/${sessionId}/hardening/operations/complete`,
            { path, method }
        );
        return {
            success: true,
            data: response.data,
        };
    } catch (error) {
        return handleApiError(error, "Failed to harden operation completely");
    }
};

export const getHardeningPatterns = async () => {
    try {
        const response = await axios.get(
            `${API_CONFIG.BASE_URL}/sessions/dummy/hardening/patterns`
        );
        return {
            success: true,
            data: response.data,
        };
    } catch (error) {
        return handleApiError(error, "Failed to get hardening patterns");
    }
};

// Test Case Generation Services
export const generateTestCases = async (testRequest) => {
    if (!testRequest) {
        return {
            success: false,
            error: "Test request is required",
            type: ERROR_TYPES.VALIDATION_ERROR
        };
    }

    try {
        const response = await axios.post(
            `${API_CONFIG.BASE_URL}/proxy/request`,
            {
                url: "/ai/test-cases/generate",
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: testRequest
            }
        );
        return {
            success: true,
            data: response.data.body,
        };
    } catch (error) {
        return handleApiError(error, "Failed to generate test cases");
    }
};

export const generateTestSuite = async (specText, options = {}) => {
    if (!specText) {
        return {
            success: false,
            error: "Specification text is required",
            type: ERROR_TYPES.VALIDATION_ERROR
        };
    }

    try {
        const request = {
            spec_text: specText,
            options: {
                test_types: options.testTypes || ["positive", "negative", "edge_cases"],
                max_operations: options.maxOperations || 10,
                ...options
            }
        };

        const response = await axios.post(
            `${API_CONFIG.BASE_URL}/proxy/request`,
            {
                url: "/ai/test-suite/generate",
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: request
            }
        );
        return {
            success: true,
            data: response.data.body,
        };
    } catch (error) {
        return handleApiError(error, "Failed to generate test suite");
    }
};

export const generateOperationTestCases = async (sessionId, path, method, operationSummary) => {
    if (!sessionId || !path || !method) {
        return {
            success: false,
            error: "Session ID, path, and method are required",
            type: ERROR_TYPES.VALIDATION_ERROR
        };
    }

    try {
        // Get spec from session first
        const specResult = await getSessionSpec(sessionId);
        if (!specResult.success) {
            return specResult;
        }

        const testRequest = {
            spec_text: JSON.stringify(specResult.data),
            path: path,
            method: method,
            operation_summary: operationSummary || `${method.toUpperCase()} ${path}`,
            test_types: ["positive", "negative", "edge_cases"]
        };

        return await generateTestCases(testRequest);
    } catch (error) {
        return handleApiError(error, "Failed to generate test cases for operation");
    }
};

/**
 * Perform AI meta-analysis on linter findings.
 * This is the "linter-augmented AI analyst" feature.
 */
export const performAIMetaAnalysis = async (sessionId) => {
    if (!sessionId) {
        return {
            success: false,
            error: "Session ID is required",
            type: ERROR_TYPES.VALIDATION_ERROR
        };
    }

    try {
        const response = await axios.post(
            `${API_CONFIG.BASE_URL}/sessions/${sessionId}/spec/ai-analysis`,
            {},
            {
                timeout: 60000 // 60 second timeout for AI analysis
            }
        );
        return {
            success: true,
            data: response.data,
        };
    } catch (error) {
        return handleApiError(error, "AI meta-analysis failed");
    }
};

/**
 * Analyze description quality for all operations and schemas.
 * Returns quality scores and JSON Patch operations for improvements.
 */
export const analyzeDescriptions = async (sessionId) => {
    if (!sessionId) {
        return {
            success: false,
            error: "Session ID is required",
            type: ERROR_TYPES.VALIDATION_ERROR
        };
    }

    try {
        const response = await axios.post(
            `${API_CONFIG.BASE_URL}/sessions/${sessionId}/spec/analyze-descriptions`,
            {},
            {
                timeout: 60000 // 60 second timeout for AI analysis
            }
        );
        return {
            success: true,
            data: response.data,
        };
    } catch (error) {
        return handleApiError(error, "Description analysis failed");
    }
};
