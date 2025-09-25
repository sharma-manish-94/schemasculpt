import {
    executeAiAction,
    processSpecification,
    processSpecificationStreaming,
    generateSpecification,
    getAgentsStatus,
    getSpecificAgentStatus,
    restartAgent,
    getAgentsPerformance,
    getAgentsCapabilities,
    generateIntelligentPrompt,
    getPromptStatistics,
    usePromptTemplate,
    getAvailableTemplates,
    optimizePrompt,
    executeWorkflow,
    executeCustomWorkflow,
    getAvailableWorkflows,
    aiHealthCheck
} from "../../api/aiService";
import {useSpecStore} from "../specStore";

export const createAiSlice = (set, get) => ({

    // --- STATE ---
    aiPrompt: '',
    aiResponse: null,
    aiError: null,
    isAiProcessing: false,
    isStreaming: false,
    streamingChunks: [],

    // Agent status
    agentsStatus: null,
    agentsPerformance: null,
    agentsCapabilities: null,

    // Prompt management
    promptStatistics: null,
    availableTemplates: null,
    availableWorkflows: null,

    // AI health
    aiHealthStatus: null,

    // --- ACTIONS ---

    setAiPrompt: (prompt) => set({aiPrompt: prompt}),

    clearAiResponse: () => set({
        aiResponse: null,
        aiError: null,
        streamingChunks: []
    }),

    // Legacy support
    submitAIRequest: async () => {
        const { sessionId, aiPrompt, setSpecText } = useSpecStore.getState();
        if (!aiPrompt.trim() || !sessionId) return;

        set({isAiProcessing: true, aiError: null});
        const result = await executeAiAction(sessionId, aiPrompt);

        if(result && result.success) {
            const updatedSpecText = JSON.stringify(result.data, null, 2);
            setSpecText(updatedSpecText);
            set({aiResponse: result.data});
        } else {
            set({aiError: result?.error || 'Unknown error occurred'});
        }

        set({aiPrompt: '', isAiProcessing: false});
    },

    // Enhanced AI Processing
    processSpecification: async (request) => {
        set({isAiProcessing: true, aiError: null, aiResponse: null});

        const result = await processSpecification(request);

        if (result.success) {
            set({
                aiResponse: result.data,
                isAiProcessing: false
            });
        } else {
            set({
                aiError: result.error,
                isAiProcessing: false
            });
        }

        return result;
    },

    processSpecificationStreaming: async (request, onUpdate) => {
        set({
            isStreaming: true,
            isAiProcessing: true,
            aiError: null,
            streamingChunks: []
        });

        const onChunk = (chunk) => {
            set(state => ({
                streamingChunks: [...state.streamingChunks, chunk]
            }));
            onUpdate?.(chunk);
        };

        const onComplete = () => {
            set({
                isStreaming: false,
                isAiProcessing: false
            });
        };

        const onError = (error) => {
            set({
                isStreaming: false,
                isAiProcessing: false,
                aiError: error.error || 'Streaming failed'
            });
        };

        return processSpecificationStreaming(request, onChunk, onComplete, onError);
    },

    generateSpecification: async (request) => {
        set({isAiProcessing: true, aiError: null, aiResponse: null});

        const result = await generateSpecification(request);

        if (result.success) {
            set({
                aiResponse: result.data,
                isAiProcessing: false
            });

            // Update spec store if we have a new specification
            if (result.data?.generatedSpec) {
                const { setSpecText } = useSpecStore.getState();
                setSpecText(result.data.generatedSpec);
            }
        } else {
            set({
                aiError: result.error,
                isAiProcessing: false
            });
        }

        return result;
    },

    // Agent Management
    fetchAgentsStatus: async () => {
        const result = await getAgentsStatus();
        if (result.success) {
            set({agentsStatus: result.data});
        }
        return result;
    },

    fetchSpecificAgentStatus: async (agentName) => {
        return await getSpecificAgentStatus(agentName);
    },

    restartAgent: async (agentName) => {
        return await restartAgent(agentName);
    },

    fetchAgentsPerformance: async () => {
        const result = await getAgentsPerformance();
        if (result.success) {
            set({agentsPerformance: result.data});
        }
        return result;
    },

    fetchAgentsCapabilities: async () => {
        const result = await getAgentsCapabilities();
        if (result.success) {
            set({agentsCapabilities: result.data});
        }
        return result;
    },

    // Prompt Management
    generateIntelligentPrompt: async (requestData, contextId) => {
        return await generateIntelligentPrompt(requestData, contextId);
    },

    fetchPromptStatistics: async () => {
        const result = await getPromptStatistics();
        if (result.success) {
            set({promptStatistics: result.data});
        }
        return result;
    },

    usePromptTemplate: async (templateName, variables) => {
        return await usePromptTemplate(templateName, variables);
    },

    fetchAvailableTemplates: async () => {
        const result = await getAvailableTemplates();
        if (result.success) {
            set({availableTemplates: result.data});
        }
        return result;
    },

    optimizePrompt: async (promptData) => {
        return await optimizePrompt(promptData);
    },

    // Workflow Management
    executeWorkflow: async (workflowName, inputData) => {
        set({isAiProcessing: true, aiError: null});

        const result = await executeWorkflow(workflowName, inputData);

        if (result.success) {
            set({
                aiResponse: result.data,
                isAiProcessing: false
            });
        } else {
            set({
                aiError: result.error,
                isAiProcessing: false
            });
        }

        return result;
    },

    executeCustomWorkflow: async (workflowDefinition) => {
        set({isAiProcessing: true, aiError: null});

        const result = await executeCustomWorkflow(workflowDefinition);

        if (result.success) {
            set({
                aiResponse: result.data,
                isAiProcessing: false
            });
        } else {
            set({
                aiError: result.error,
                isAiProcessing: false
            });
        }

        return result;
    },

    fetchAvailableWorkflows: async () => {
        const result = await getAvailableWorkflows();
        if (result.success) {
            set({availableWorkflows: result.data});
        }
        return result;
    },

    // Health Check
    checkAiHealth: async () => {
        const result = await aiHealthCheck();
        if (result.success) {
            set({aiHealthStatus: result.data});
        }
        return result;
    }
});