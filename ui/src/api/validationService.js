import axios from "axios";

const API_BASE_URL = 'http://localhost:8080/api/v1';

/**
 * Validates the provided OpenAPI specification string by calling the backend API.
 * @param {string} specText The OpenAPI spec content as a string.
 * @returns {Promise<{success: boolean, data: Array, error: string|null}>} A promise that resolves to an object indicating success or failure.
 */
export const validateSpec = async (specText) => {
    try {
        const response = await axios.post(`${API_BASE_URL}/validate`, {
            spec: specText
        });
        return { success: true, data: response.data, error: null };
    } catch (error) {
        console.error("Error validating spec:", error)
        return { success: false, data: [], error: "Failed to connect to the validation service." };
    }
}

export const applyQuickFix = async (fixRequest) => {
    try {
        const response = await axios.post(`${API_BASE_URL}/fix`, fixRequest);
        return response.data; // Should be { updatedSpecText: "..." }
    } catch (error) {
        console.error("Error applying fix:", error);
        return null;
    }
};

export const executeAiAction = async (specText, prompt) => {
    try{
        const response = await axios.post(`${API_BASE_URL}/ai/execute`, {
            prompt: prompt,
            specText: specText
        });
        return response.data;
    } catch (error) {
        console.error("Error execute AI Action:", error);
        return { updatedSpecText: `Error: Could not connect to the AI service.\n\nDetails:\n${error.message}` };
    }
}