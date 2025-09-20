import {
    executeProxyRequest,
    startMockServer as apiStartMockServer,
    refreshMockSpec,
    getOperationDetails
} from "../../api/validationService";
import { buildRequestDetails } from "../../utils/requestBuilder";
import { parseEndpointsFromSpec } from "../../utils/specParser";
import { REQUEST_CONFIG } from "../../config/constants";
import { LOADING_STATES, ERROR_TYPES } from "../types";
import { useResponseStore } from "../responseStore";

const initialRequestState = {
    // Navigation state
    selectedNavItem: null,
    selectedNavItemDetails: null,
    isNavItemLoading: false,

    // Mock server state
    mockServer: {
        active: false,
        url: "",
        id: ""
    },

    // Request configuration
    serverTarget: REQUEST_CONFIG.SERVER_TARGETS.MOCK,
    customServerUrl: "",
    pathParams: {},
    requestBody: "",

    // Endpoints
    endpoints: [],

    // Error state
    error: null,
    loadingState: LOADING_STATES.IDLE
};

export const createRequestSlice = (set, get) => ({
    ...initialRequestState,

    // Navigation Actions
    setSelectedNavItem: async (item) => {
        try {
            if (!item) {
                set({
                    selectedNavItem: null,
                    selectedNavItemDetails: null,
                    error: null
                });
                return;
            }

            set({
                selectedNavItem: item,
                isNavItemLoading: true,
                selectedNavItemDetails: null,
                error: null
            });

            // Get session ID from current state (since this slice is integrated with specStore)
            const { sessionId } = get();

            if (sessionId && item.path && item.method) {
                const result = await getOperationDetails(sessionId, item.path, item.method);

                if (result.success) {
                    set({
                        selectedNavItemDetails: result.data,
                        error: null
                    });
                } else {
                    set({
                        error: {
                            type: ERROR_TYPES.SERVER_ERROR,
                            message: result.error || "Failed to load operation details"
                        }
                    });
                }
            }
        } catch (error) {
            set({
                error: {
                    type: ERROR_TYPES.NETWORK_ERROR,
                    message: error.message || "Network error occurred"
                }
            });
        } finally {
            set({ isNavItemLoading: false });
        }
    },

    // Endpoint parsing
    parseEndpoints: () => {
        try {
            const { specText } = get();
            const availableEndpoints = parseEndpointsFromSpec(specText);
            set({
                endpoints: availableEndpoints,
                error: null
            });
        } catch (error) {
            set({
                error: {
                    type: ERROR_TYPES.PARSING_ERROR,
                    message: "Failed to parse endpoints from specification"
                }
            });
        }
    },

    // Mock server management
    startMockServer: async () => {
        try {
            set({ loadingState: LOADING_STATES.LOADING });

            const { specText } = get();
            const result = await apiStartMockServer(specText);

            if (result?.success && result?.data) {
                set({
                    mockServer: {
                        active: true,
                        url: result.data.mockUrl,
                        id: result.data.sessionId
                    },
                    loadingState: LOADING_STATES.SUCCESS,
                    error: null
                });
                return { success: true };
            } else {
                const errorMessage = result.error || "Failed to start mock server";
                set({
                    loadingState: LOADING_STATES.ERROR,
                    error: {
                        type: ERROR_TYPES.SERVER_ERROR,
                        message: errorMessage
                    }
                });
                return { success: false, error: errorMessage };
            }
        } catch (error) {
            const errorMessage = error.message || "Network error starting mock server";
            set({
                loadingState: LOADING_STATES.ERROR,
                error: {
                    type: ERROR_TYPES.NETWORK_ERROR,
                    message: errorMessage
                }
            });
            return { success: false, error: errorMessage };
        }
    },

    refreshMockServer: async () => {
        try {
            const { mockServer, specText } = get();

            if (!mockServer.active) {
                throw new Error("Mock server is not active");
            }

            set({ loadingState: LOADING_STATES.LOADING });

            const result = await refreshMockSpec(mockServer.id, specText);

            if (result.success) {
                set({
                    loadingState: LOADING_STATES.SUCCESS,
                    error: null
                });
                return { success: true, message: "Mock server spec updated successfully" };
            } else {
                const errorMessage = result.error || "Failed to refresh mock server";
                set({
                    loadingState: LOADING_STATES.ERROR,
                    error: {
                        type: ERROR_TYPES.SERVER_ERROR,
                        message: errorMessage
                    }
                });
                return { success: false, error: errorMessage };
            }
        } catch (error) {
            const errorMessage = error.message || "Error refreshing mock server";
            set({
                loadingState: LOADING_STATES.ERROR,
                error: {
                    type: ERROR_TYPES.NETWORK_ERROR,
                    message: errorMessage
                }
            });
            return { success: false, error: errorMessage };
        }
    },

    // Request configuration setters
    setServerTarget: (target) => {
        if (Object.values(REQUEST_CONFIG.SERVER_TARGETS).includes(target)) {
            set({ serverTarget: target, error: null });
        } else {
            set({
                error: {
                    type: ERROR_TYPES.VALIDATION_ERROR,
                    message: "Invalid server target"
                }
            });
        }
    },

    setCustomServerUrl: (url) => {
        set({ customServerUrl: url, error: null });
    },

    setPathParams: (params) => {
        set({ pathParams: params || {}, error: null });
    },

    setRequestBody: (body) => {
        set({ requestBody: body || "", error: null });
    },

    // Request execution
    sendRequest: async (endpoints, mockServer) => {
        try {
            const requestState = { ...get(), endpoints, mockServer };
            const endpoint = requestState.selectedNavItem;

            if (!endpoint) {
                throw new Error("No operation selected");
            }

            const { error, request } = buildRequestDetails(endpoint, requestState);

            if (error) {
                set({
                    error: {
                        type: ERROR_TYPES.VALIDATION_ERROR,
                        message: error
                    }
                });
                return { success: false, error };
            }

            // Start request in response store
            const { startRequest, setResponse } = useResponseStore.getState();
            startRequest();

            const result = await executeProxyRequest(request);
            setResponse(result);

            return { success: true, result };
        } catch (error) {
            const errorMessage = error.message || "Failed to send request";
            set({
                error: {
                    type: ERROR_TYPES.NETWORK_ERROR,
                    message: errorMessage
                }
            });
            return { success: false, error: errorMessage };
        }
    },

    // Error management
    clearError: () => set({ error: null }),

    // Reset state
    resetRequestState: () => set(initialRequestState)
});