import { create } from 'zustand';
import { useSpecStore } from './specStore';
import { useResponseStore } from './responseStore'; // Import the response store
import { executeProxyRequest, startMockServer as apiStartMockServer, refreshMockSpec } from '../api/validationService';
import yaml from "js-yaml";

export const useRequestStore = create((set, get) => ({
    // --- STATE ---
    mockServer: { active: false, url: '', id: '' },
    endpoints:[],
    selectedEndpointIndex: '',
    serverTarget: 'mock',
    customServerUrl: '',
    pathParams: {},
    requestBody: '',

    // --- ACTIONS ---

    parseEndpoints: () => {
        try {
            const { specText } = useSpecStore.getState(); // Get specText from the main store
            const specObject = yaml.load(specText);
            const availableEndpoints = [];
            if (specObject && specObject.paths) {
                for (const path in specObject.paths) {
                    for (const method in specObject.paths[path]) {
                        if (['get', 'post', 'put', 'delete', 'patch', 'options', 'head'].includes(method.toLowerCase())) {
                            availableEndpoints.push({
                                path,
                                method: method.toUpperCase(),
                                details: specObject.paths[path][method]
                            });
                        }
                    }
                }
            }
            set({ endpoints: availableEndpoints, selectedEndpointIndex: '' });
        } catch (e) {
            set({ endpoints: [] });
        }
    },

    startMockServer: async () => {
        const { specText } = useSpecStore.getState();
        const result = await apiStartMockServer(specText);
        if (result?.success && result?.data) {
            set({
                mockServer: { active: true, url: result.data.mockUrl, id: result.data.sessionId },
            });
            return true; // Return success
        } else {
            alert(`Error: ${result.error || "An unknown error occurred."}`);
            return false; // Return failure
        }
    },

    refreshMockServer: async () => {
        const { mockServer, specText } = get();
        if (!mockServer.active) return;
        const result = await refreshMockSpec(mockServer.id, specText);
        if (result.success) {
            alert("Mock server spec updated successfully.");
        } else {
            alert(`Error: ${result.error}`);
        }
    },

    setSelectedEndpointIndex: (index) => set({
        selectedEndpointIndex: index,
        pathParams: {}, // Reset params and body when endpoint changes
        requestBody: '',
        ...useResponseStore.getState().setResponse(null)
    }),
    setServerTarget: (target) => set({ serverTarget: target }),
    setCustomServerUrl: (url) => set({ customServerUrl: url }),
    setPathParams: (params) => set({ pathParams: params }),
    setRequestBody: (body) => set({ requestBody: body }),

    // This action now orchestrates the call and uses the response store
    sendRequest: async (endpoints, mockServer) => {
        const { startRequest, setResponse } = useResponseStore.getState();
        const { selectedEndpointIndex, serverTarget, customServerUrl, pathParams, requestBody } = get();

        const endpoint = endpoints[selectedEndpointIndex];
        if (!endpoint) {
            alert("Please select an endpoint first.");
            return;
        }

        let baseUrl = serverTarget === 'mock' ? mockServer.url : customServerUrl;
        if ((serverTarget === 'mock' && !mockServer.active) || !baseUrl) {
            alert("Please configure a target server URL.");
            return;
        }

        let finalUrl = baseUrl + endpoint.path;
        for (const paramName in pathParams) {
            finalUrl = finalUrl.replace(`{${paramName}}`, pathParams[paramName]);
        }

        startRequest(); // Tell the response store we are now loading
        const result = await executeProxyRequest({
            method: endpoint.method,
            url: finalUrl,
            headers: { 'Content-Type': 'application/json' },
            body: requestBody || null,
        });
        setResponse(result); // Set the final result in the response store
    },
}));