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
