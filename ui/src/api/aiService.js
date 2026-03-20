import axios from "axios";
import { API_CONFIG, REQUEST_CONFIG } from "../config/constants";
import { ERROR_TYPES } from "../store/types";

axios.defaults.timeout = REQUEST_CONFIG.DEFAULT_TIMEOUT;

const handleApiError = (error, fallbackMessage) => {
  console.error(fallbackMessage, error);

  if (error.code === "ECONNABORTED") {
    return {
      success: false,
      error: "Request timeout - please try again",
      type: ERROR_TYPES.TIMEOUT_ERROR,
    };
  }

  if (error.response) {
    return {
      success: false,
      error:
        error.response.data?.detail ||
        error.response.data?.message ||
        fallbackMessage,
      type: ERROR_TYPES.SERVER_ERROR,
      statusCode: error.response.status,
    };
  }

  if (error.request) {
    return {
      success: false,
      error: "Unable to connect to AI service",
      type: ERROR_TYPES.NETWORK_ERROR,
    };
  }

  return {
    success: false,
    error: error.message || fallbackMessage,
    type: ERROR_TYPES.NETWORK_ERROR,
  };
};

// AI Processing Service
export const processSpecification = async (request) => {
  if (!request || !request.operationType) {
    return {
      success: false,
      error: "Operation type is required",
      type: ERROR_TYPES.VALIDATION_ERROR,
    };
  }

  try {
    const response = await axios.post(
      `${API_CONFIG.BASE_URL}/ai/process`,
      request,
    );
    return {
      success: true,
      data: response.data,
    };
  } catch (error) {
    return handleApiError(error, "AI processing failed");
  }
};

export const processSpecificationStreaming = async (
  request,
  onChunk,
  onComplete,
  onError,
) => {
  if (!request || !request.operationType) {
    onError?.({
      success: false,
      error: "Operation type is required",
      type: ERROR_TYPES.VALIDATION_ERROR,
    });
    return;
  }

  try {
    const eventSource = new EventSource(
      `${API_CONFIG.BASE_URL}/ai/process/stream`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(request),
      },
    );

    eventSource.onmessage = (event) => {
      if (event.data) {
        try {
          const data = JSON.parse(event.data);
          onChunk?.(data);
        } catch (e) {
          onChunk?.(event.data);
        }
      }
    };

    eventSource.addEventListener("complete", (event) => {
      eventSource.close();
      onComplete?.();
    });

    eventSource.onerror = (error) => {
      eventSource.close();
      onError?.(handleApiError(error, "Streaming AI processing failed"));
    };

    return eventSource;
  } catch (error) {
    onError?.(handleApiError(error, "Failed to start streaming"));
  }
};

export const generateSpecification = async (request) => {
  if (!request || !request.domain) {
    return {
      success: false,
      error: "Domain is required for specification generation",
      type: ERROR_TYPES.VALIDATION_ERROR,
    };
  }

  try {
    const response = await axios.post(
      `${API_CONFIG.BASE_URL}/ai/generate`,
      request,
    );
    return {
      success: true,
      data: response.data,
    };
  } catch (error) {
    return handleApiError(error, "Specification generation failed");
  }
};

// AI Agent Service
export const getAgentsStatus = async () => {
  try {
    const response = await axios.get(`${API_CONFIG.BASE_URL}/ai/agents/status`);
    return {
      success: true,
      data: response.data,
    };
  } catch (error) {
    return handleApiError(error, "Failed to fetch agents status");
  }
};

export const getSpecificAgentStatus = async (agentName) => {
  if (!agentName) {
    return {
      success: false,
      error: "Agent name is required",
      type: ERROR_TYPES.VALIDATION_ERROR,
    };
  }

  try {
    const response = await axios.get(
      `${API_CONFIG.BASE_URL}/ai/agents/${agentName}/status`,
    );
    return {
      success: true,
      data: response.data,
    };
  } catch (error) {
    return handleApiError(
      error,
      `Failed to fetch status for agent ${agentName}`,
    );
  }
};

export const restartAgent = async (agentName) => {
  if (!agentName) {
    return {
      success: false,
      error: "Agent name is required",
      type: ERROR_TYPES.VALIDATION_ERROR,
    };
  }

  try {
    const response = await axios.post(
      `${API_CONFIG.BASE_URL}/ai/agents/${agentName}/restart`,
    );
    return {
      success: true,
      data: response.data,
    };
  } catch (error) {
    return handleApiError(error, `Failed to restart agent ${agentName}`);
  }
};

export const getAgentsPerformance = async () => {
  try {
    const response = await axios.get(
      `${API_CONFIG.BASE_URL}/ai/agents/performance`,
    );
    return {
      success: true,
      data: response.data,
    };
  } catch (error) {
    return handleApiError(error, "Failed to fetch agents performance");
  }
};

export const getAgentsCapabilities = async () => {
  try {
    const response = await axios.get(
      `${API_CONFIG.BASE_URL}/ai/agents/capabilities`,
    );
    return {
      success: true,
      data: response.data,
    };
  } catch (error) {
    return handleApiError(error, "Failed to fetch agents capabilities");
  }
};

// AI Prompt Service
export const generateIntelligentPrompt = async (
  requestData,
  contextId = null,
) => {
  if (!requestData) {
    return {
      success: false,
      error: "Request data is required",
      type: ERROR_TYPES.VALIDATION_ERROR,
    };
  }

  try {
    const url = contextId
      ? `${API_CONFIG.BASE_URL}/ai/prompt/generate?contextId=${contextId}`
      : `${API_CONFIG.BASE_URL}/ai/prompt/generate`;

    const response = await axios.post(url, requestData);
    return {
      success: true,
      data: response.data,
    };
  } catch (error) {
    return handleApiError(error, "Failed to generate intelligent prompt");
  }
};

export const getPromptStatistics = async () => {
  try {
    const response = await axios.get(
      `${API_CONFIG.BASE_URL}/ai/prompt/statistics`,
    );
    return {
      success: true,
      data: response.data,
    };
  } catch (error) {
    return handleApiError(error, "Failed to fetch prompt statistics");
  }
};

export const usePromptTemplate = async (templateName, templateVariables) => {
  if (!templateName) {
    return {
      success: false,
      error: "Template name is required",
      type: ERROR_TYPES.VALIDATION_ERROR,
    };
  }

  try {
    const response = await axios.post(
      `${API_CONFIG.BASE_URL}/ai/prompt/template/${templateName}`,
      templateVariables || {},
    );
    return {
      success: true,
      data: response.data,
    };
  } catch (error) {
    return handleApiError(
      error,
      `Failed to use prompt template ${templateName}`,
    );
  }
};

export const getAvailableTemplates = async () => {
  try {
    const response = await axios.get(
      `${API_CONFIG.BASE_URL}/ai/prompt/templates`,
    );
    return {
      success: true,
      data: response.data,
    };
  } catch (error) {
    return handleApiError(error, "Failed to fetch available templates");
  }
};

export const optimizePrompt = async (promptData) => {
  if (!promptData || !promptData.prompt) {
    return {
      success: false,
      error: "Prompt text is required",
      type: ERROR_TYPES.VALIDATION_ERROR,
    };
  }

  try {
    const response = await axios.post(
      `${API_CONFIG.BASE_URL}/ai/prompt/optimize`,
      promptData,
    );
    return {
      success: true,
      data: response.data,
    };
  } catch (error) {
    return handleApiError(error, "Failed to optimize prompt");
  }
};

// AI Workflow Service
export const executeWorkflow = async (workflowName, inputData) => {
  if (!workflowName) {
    return {
      success: false,
      error: "Workflow name is required",
      type: ERROR_TYPES.VALIDATION_ERROR,
    };
  }

  try {
    const response = await axios.post(
      `${API_CONFIG.BASE_URL}/ai/workflow/${workflowName}`,
      inputData || {},
    );
    return {
      success: true,
      data: response.data,
    };
  } catch (error) {
    return handleApiError(error, `Failed to execute workflow ${workflowName}`);
  }
};

export const executeCustomWorkflow = async (workflowDefinition) => {
  if (!workflowDefinition) {
    return {
      success: false,
      error: "Workflow definition is required",
      type: ERROR_TYPES.VALIDATION_ERROR,
    };
  }

  try {
    const response = await axios.post(
      `${API_CONFIG.BASE_URL}/ai/workflow/custom`,
      workflowDefinition,
    );
    return {
      success: true,
      data: response.data,
    };
  } catch (error) {
    return handleApiError(error, "Failed to execute custom workflow");
  }
};

export const getAvailableWorkflows = async () => {
  try {
    const response = await axios.get(`${API_CONFIG.BASE_URL}/ai/workflows`);
    return {
      success: true,
      data: response.data,
    };
  } catch (error) {
    return handleApiError(error, "Failed to fetch available workflows");
  }
};

// AI Health Check
export const aiHealthCheck = async () => {
  try {
    const response = await axios.get(`${API_CONFIG.BASE_URL}/ai/health`);
    return {
      success: true,
      data: response.data,
    };
  } catch (error) {
    return handleApiError(error, "AI health check failed");
  }
};

// Legacy compatibility - keep existing executeAiAction for backward compatibility
export const executeAiAction = async (sessionId, prompt) => {
  if (!sessionId || !prompt) {
    return {
      success: false,
      error: "Session ID and prompt are required",
      type: ERROR_TYPES.VALIDATION_ERROR,
    };
  }

  try {
    const url = `${API_CONFIG.BASE_URL}/sessions/${sessionId}/spec/transform`;
    const response = await axios.post(url, { prompt });
    return {
      success: true,
      data: response.data,
    };
  } catch (error) {
    return {
      success: false,
      updatedSpecText: `Error: Could not connect to the AI service.\n\nDetails:\n${error.message}`,
    };
  }
};
