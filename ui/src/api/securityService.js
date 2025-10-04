/**
 * Security Analysis Service
 * Handles API calls for multi-agent security analysis of OpenAPI specs
 */

import axios from 'axios';

const AI_SERVICE_URL = process.env.REACT_APP_AI_SERVICE_URL || 'http://localhost:8000';

/**
 * Run comprehensive security analysis on OpenAPI specification
 * @param {string} specText - OpenAPI spec as JSON/YAML string
 * @param {boolean} forceRefresh - Force fresh analysis, bypass cache
 * @param {Array} validationSuggestions - Optional validation suggestions for context
 * @returns {Promise<Object>} Security analysis report
 */
export const runSecurityAnalysis = async (specText, forceRefresh = false, validationSuggestions = null) => {
    try {
        const requestBody = {
            spec_text: specText,
            force_refresh: forceRefresh
        };

        // Add validation suggestions if provided
        if (validationSuggestions && validationSuggestions.length > 0) {
            requestBody.validation_suggestions = validationSuggestions.map(s => ({
                rule_id: s.ruleId,
                message: s.message,
                severity: s.severity || 'info',
                path: s.path,
                category: s.category
            }));
        }

        const response = await axios.post(`${AI_SERVICE_URL}/ai/security/analyze`, requestBody);

        return {
            success: true,
            cached: response.data.cached,
            report: response.data.report,
            correlationId: response.data.correlation_id
        };
    } catch (error) {
        console.error('Security analysis failed:', error);
        return {
            success: false,
            error: error.response?.data?.detail?.message || error.message
        };
    }
};

/**
 * Run authentication-only analysis
 * @param {string} specText - OpenAPI spec as JSON/YAML string
 * @returns {Promise<Object>} Authentication analysis result
 */
export const analyzeAuthentication = async (specText) => {
    try {
        const response = await axios.post(`${AI_SERVICE_URL}/ai/security/analyze/authentication`, {
            spec_text: specText
        });

        return {
            success: true,
            analysis: response.data.analysis,
            correlationId: response.data.correlation_id
        };
    } catch (error) {
        console.error('Authentication analysis failed:', error);
        return {
            success: false,
            error: error.response?.data?.detail?.message || error.message
        };
    }
};

/**
 * Run authorization-only analysis
 * @param {string} specText - OpenAPI spec as JSON/YAML string
 * @returns {Promise<Object>} Authorization analysis result
 */
export const analyzeAuthorization = async (specText) => {
    try {
        const response = await axios.post(`${AI_SERVICE_URL}/ai/security/analyze/authorization`, {
            spec_text: specText
        });

        return {
            success: true,
            analysis: response.data.analysis,
            correlationId: response.data.correlation_id
        };
    } catch (error) {
        console.error('Authorization analysis failed:', error);
        return {
            success: false,
            error: error.response?.data?.detail?.message || error.message
        };
    }
};

/**
 * Run data exposure analysis
 * @param {string} specText - OpenAPI spec as JSON/YAML string
 * @returns {Promise<Object>} Data exposure analysis result
 */
export const analyzeDataExposure = async (specText) => {
    try {
        const response = await axios.post(`${AI_SERVICE_URL}/ai/security/analyze/data-exposure`, {
            spec_text: specText
        });

        return {
            success: true,
            analysis: response.data.analysis,
            correlationId: response.data.correlation_id
        };
    } catch (error) {
        console.error('Data exposure analysis failed:', error);
        return {
            success: false,
            error: error.response?.data?.detail?.message || error.message
        };
    }
};

/**
 * Get cached security report by spec hash
 * @param {string} specHash - Hash of the OpenAPI spec
 * @returns {Promise<Object>} Cached security report
 */
export const getCachedSecurityReport = async (specHash) => {
    try {
        const response = await axios.get(`${AI_SERVICE_URL}/ai/security/report/${specHash}`);

        return {
            success: true,
            cached: response.data.cached,
            report: response.data.report,
            specHash: response.data.spec_hash
        };
    } catch (error) {
        if (error.response?.status === 404) {
            return {
                success: false,
                notFound: true,
                error: 'No cached report found'
            };
        }

        console.error('Failed to retrieve cached report:', error);
        return {
            success: false,
            error: error.response?.data?.detail?.message || error.message
        };
    }
};

/**
 * Get security cache statistics
 * @returns {Promise<Object>} Cache statistics
 */
export const getSecurityCacheStats = async () => {
    try {
        const response = await axios.get(`${AI_SERVICE_URL}/ai/security/cache/stats`);

        return {
            success: true,
            stats: response.data
        };
    } catch (error) {
        console.error('Failed to get cache stats:', error);
        return {
            success: false,
            error: error.response?.data?.detail?.message || error.message
        };
    }
};

/**
 * Clear security analysis cache
 * @returns {Promise<Object>} Clear cache result
 */
export const clearSecurityCache = async () => {
    try {
        const response = await axios.delete(`${AI_SERVICE_URL}/ai/security/cache/clear`);

        return {
            success: true,
            cleared: response.data.cleared,
            message: response.data.message
        };
    } catch (error) {
        console.error('Failed to clear cache:', error);
        return {
            success: false,
            error: error.response?.data?.detail?.message || error.message
        };
    }
};
