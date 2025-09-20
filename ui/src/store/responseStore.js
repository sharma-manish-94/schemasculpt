import { create } from 'zustand';
import { LOADING_STATES, ERROR_TYPES } from './types';

const initialResponseState = {
    apiResponse: null,
    isApiRequestLoading: false,
    requestHistory: [],
    loadingState: LOADING_STATES.IDLE,
    error: null
};

export const useResponseStore = create((set, get) => ({
    ...initialResponseState,

    // Request lifecycle management
    startRequest: () => {
        set({
            isApiRequestLoading: true,
            apiResponse: null,
            loadingState: LOADING_STATES.LOADING,
            error: null
        });
    },

    setResponse: (response) => {
        const timestamp = new Date().toISOString();
        const { requestHistory } = get();

        // Add to history (keep last 10 requests)
        const newHistory = [
            { ...response, timestamp },
            ...requestHistory.slice(0, 9)
        ];

        set({
            apiResponse: response,
            isApiRequestLoading: false,
            requestHistory: newHistory,
            loadingState: response.success ? LOADING_STATES.SUCCESS : LOADING_STATES.ERROR,
            error: response.success ? null : {
                type: ERROR_TYPES.SERVER_ERROR,
                message: response.error || 'Request failed'
            }
        });
    },

    // Request history management
    clearRequestHistory: () => {
        set({ requestHistory: [] });
    },

    // Error management
    clearError: () => {
        set({ error: null });
    },

    // Reset state
    resetResponseState: () => {
        set(initialResponseState);
    }
}));