import axios from "axios";

const API_BASE_URL = 'http://localhost:8080/api/v1';

export const validateSpec = async (specText) => {
    try {
        const response = await axios.post(`${API_BASE_URL}/validate`, {
            spec: specText
        });
        return response.data;
    } catch (error) {
        console.error("Error validating spec:", error)
        return [];
    }
}