import {startMockServer, refreshMockSpec, executeProxyRequest} from '../../api/validationService';
import yaml from 'js-yaml';

export const createApiLabSlice = (set, get) => ({
    // --- STATE ---
    endpoints: [],
    selectedEndpointIndex: '',
    serverTarget: 'mock',
    customServerUrl: '',
    mockServer: {active: false, url: '', id: ''},
    pathParams: {},
    requestBody: '',
    apiResponse: null,
    isApiRequestLoading: false,

    // --- ACTIONS ---
    parseEndpoints: () => {
        try {
            const specObject = yaml.load(get().specText);
            const availableEndpoints = [];
            if (specObject && specObject.paths) {
                for (const path in specObject.paths) {
                    for (const method in specObject.paths[path]) {
                        if (['get', 'post', 'put', 'delete', 'patch', 'options', 'head'].includes(method.toLowerCase())) {
                            availableEndpoints.push({
                                path, method: method.toUpperCase(), details: specObject.paths[path][method]
                            });
                        }
                    }
                }
            }
            set({endpoints: availableEndpoints, selectedEndpointIndex: '', apiResponse: null});
        } catch (e) {
            set({endpoints: []});
        }
    },

    setSelectedEndpointIndex: (index) => set({
        selectedEndpointIndex: index,
        pathParams: {},
        requestBody: '',
        apiResponse: null
    }),
    setServerTarget: (target) => set({serverTarget: target}),
    setCustomServerUrl: (url) => set({customServerUrl: url}),
    setPathParams: (params) => set({pathParams: params}),
    setRequestBody: (body) => set({requestBody: body}),

    startMockServer: async () => {
        set({isLoading: true});
        const result = await startMockServer(get().specText);
        if (result?.success && result?.data) {
            set({
                mockServer: {active: true, url: result.data.mockUrl, id: result.data.sessionId}, activeTab: 'api_lab',
            });
        } else {
            alert(`Error: ${result.error || "An unknown error occurred."}`);
        }
        set({isLoading: false});
    },

    refreshMockServer: async () => {
        const {mockServer, specText} = get();
        if (!mockServer.active) return;
        const result = await refreshMockSpec(mockServer.id, specText);
        if (result.success) {
            alert("Mock server spec updated successfully.");
        } else {
            alert(`Error: ${result.error}`);
        }
    },

    sendRequest: async () => {
        const {
            endpoints,
            selectedEndpointIndex,
            serverTarget,
            mockServer,
            customServerUrl,
            pathParams,
            requestBody
        } = get();
        const endpoint = endpoints[selectedEndpointIndex];
        if (!endpoint) return;

        let baseUrl = serverTarget === 'mock' ? mockServer.url : customServerUrl;
        if ((serverTarget === 'mock' && !mockServer.active) || !baseUrl) {
            alert("Please configure a target server URL.");
            return;
        }

        let finalUrl = baseUrl + endpoint.path;
        for (const paramName in pathParams) {
            finalUrl = finalUrl.replace(`{${paramName}}`, pathParams[paramName]);
        }

        set({isApiRequestLoading: true, apiResponse: null});
        const result = await executeProxyRequest({
            method: endpoint.method,
            url: finalUrl,
            headers: {'Content-Type': 'application/json'},
            body: requestBody || null,
        });
        set({apiResponse: result, isApiRequestLoading: false});
    },
});