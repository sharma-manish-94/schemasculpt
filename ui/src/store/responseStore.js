import { create } from 'zustand';

export const useResponseStore = create((set) => ({
    // --- STATE ---
    apiResponse: null,
    isApiRequestLoading: false,

    // --- ACTIONS ---
    startRequest: () => set({ isApiRequestLoading: true, apiResponse: null }),
    setResponse: (response) => set({ apiResponse: response, isApiRequestLoading: false }),
}));