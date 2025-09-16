import axios from "axios";

const API_BASE_URL = 'http://localhost:8080/api/v1';

export const validateSpec = async (specText) => {
    try {
        const url  = `${API_BASE_URL}/specifications/validate`;
        const response = await axios.post(url, specText,{
           headers: {'Content-Type':'text/plain'}
        });
        return { success: true, data: response.data, error: null };
    } catch (error) {
        console.error("Error validating spec:", error)
        return { success: false, data: [], error: "Failed to connect to the validation service." };
    }
}

export const applyQuickFix = async (fixRequest) => {
    try {
        const url = `${API_BASE_URL}/specifications/fix`;
        const response = await axios.post(url, fixRequest);
        return response.data;
    } catch (error) {
        console.error("Error applying fix:", error);
        return null;
    }
};

export const executeAiAction = async (specText, prompt) => {
    try {
        const url = `${API_BASE_URL}/specifications/transform`;
        const response = await axios.post(url, {
            prompt: prompt,
            specText: specText
        });
        return response.data;
    } catch (error) {
        console.error("Error execute AI Action:", error);
        return { updatedSpecText: `Error: Could not connect to the AI service.\n\nDetails:\n${error.message}` };
    }
}

export const startMockServer = async (specText) => {
    try {
        const response = await axios.post(`${API_BASE_URL}/sessions/mock`, specText, {
            headers: {'Content-Type': 'text/plain'}
        });
        return { success: true, data: response.data };
    } catch (error) {
        console.error("Error starting mock server:", error);
        return { success: false, error: error.response?.data?.detail || "Failed to start mock server." };
    }
};

export const executeProxyRequest = async (requestDetails) => {
    try {
        const response = await axios.post(`${API_BASE_URL}/proxy/request`, requestDetails);
        return { success: true, data: response.data };
    } catch (error) {
        console.error("Error executing proxy request:", error);
        const errorResponse = error.response?.data || {
            statusCode: 500,
            body: `Could not connect to the server. Details: ${error.message}`
        };
        return { success: false, error: errorResponse };
    }
};

export const refreshMockSpec = async (mockId, specText) => {
    try {
        const response = await axios.put(`${API_BASE_URL}/sessions/${mockId}/spec`, { specText }, {
            headers: {'Content-Type': 'application/json'}
        });
        return { success: true, data: response.data };
    } catch (error) {
        console.error("Error refreshing mock spec:", error);
        return { success: false, error: "Failed to refresh mock spec." };
    }
};