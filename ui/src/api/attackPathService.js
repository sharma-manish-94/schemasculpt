/**
 * Attack Path Simulation Service
 *
 * Provides API calls for the AI-powered attack path simulation feature.
 * This feature discovers multi-step attack chains that real hackers could exploit.
 */

import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8080/api/v1';

/**
 * Run attack path simulation on the current specification
 *
 * @param {string} sessionId - Current session ID
 * @param {Object} options - Analysis options
 * @param {string} options.analysisDepth - Depth of analysis (quick, standard, comprehensive, exhaustive)
 * @param {number} options.maxChainLength - Maximum steps in an attack chain (default: 5)
 * @returns {Promise<Object>} Attack path analysis report
 */
export const runAttackPathSimulation = async (sessionId, options = {}) => {
  const {
    analysisDepth = 'standard',
    maxChainLength = 5
  } = options;

  try {
    const response = await axios.post(
      `${API_BASE_URL}/sessions/${sessionId}/analysis/attack-path-simulation`,
      null,
      {
        params: {
          analysisDepth,
          maxChainLength
        },
        timeout: 300000  // 5 minute timeout (same as backend)
      }
    );

    return response.data;
  } catch (error) {
    console.error('Attack path simulation failed:', error);
    throw error;
  }
};

/**
 * Format severity level for display
 */
export const formatSeverity = (severity) => {
  const severityMap = {
    'CRITICAL': { label: 'Critical', color: 'red', priority: 4 },
    'HIGH': { label: 'High', color: 'orange', priority: 3 },
    'MEDIUM': { label: 'Medium', color: 'yellow', priority: 2 },
    'LOW': { label: 'Low', color: 'blue', priority: 1 },
    'INFO': { label: 'Info', color: 'gray', priority: 0 }
  };

  return severityMap[severity] || severityMap['INFO'];
};

/**
 * Format risk level for display
 */
export const formatRiskLevel = (riskLevel) => {
  const riskMap = {
    'CRITICAL': { label: 'CRITICAL RISK', color: '#dc2626', bgColor: '#fee2e2' },
    'HIGH': { label: 'HIGH RISK', color: '#ea580c', bgColor: '#ffedd5' },
    'MEDIUM': { label: 'MEDIUM RISK', color: '#ca8a04', bgColor: '#fef9c3' },
    'LOW': { label: 'LOW RISK', color: '#2563eb', bgColor: '#dbeafe' }
  };

  return riskMap[riskLevel] || riskMap['MEDIUM'];
};

/**
 * Get security score color
 */
export const getSecurityScoreColor = (score) => {
  if (score >= 80) return '#16a34a'; // green
  if (score >= 60) return '#ca8a04'; // yellow
  if (score >= 40) return '#ea580c'; // orange
  return '#dc2626'; // red
};
