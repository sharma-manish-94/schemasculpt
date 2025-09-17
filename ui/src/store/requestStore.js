import { create } from "zustand";
import { useSpecStore } from "./specStore";
import { useResponseStore } from "./responseStore"; // Import the response store
import {
  executeProxyRequest,
  startMockServer as apiStartMockServer,
  refreshMockSpec,
} from "../api/validationService";
import { buildRequestDetails } from "../utils/requestBuilder";
import { parseEndpointsFromSpec } from "../utils/specParser";

export const useRequestStore = create((set, get) => ({
  // --- STATE ---
  mockServer: { active: false, url: "", id: "" },
  endpoints: [],
  serverTarget: "mock",
  customServerUrl: "",
  pathParams: {},
  requestBody: "",
  selectedNavItem: null,

  // --- ACTIONS ---

  setSelectedNavItem: (item) =>
    set({
      selectedNavItem: item,
      pathParams: {}, // Reset params when selection changes
      requestBody: "",
      ...useResponseStore.getState().setResponse(null),
    }),

  parseEndpoints: () => {
    const { specText } = useSpecStore.getState();
    const availableEndpoints = parseEndpointsFromSpec(specText);
    set({ endpoints: availableEndpoints, selectedEndpointIndex: "" });
  },

  startMockServer: async () => {
    const { specText } = useSpecStore.getState();
    const result = await apiStartMockServer(specText);
    if (result?.success && result?.data) {
      set({
        mockServer: {
          active: true,
          url: result.data.mockUrl,
          id: result.data.sessionId,
        },
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

  setServerTarget: (target) => set({ serverTarget: target }),
  setCustomServerUrl: (url) => set({ customServerUrl: url }),
  setPathParams: (params) => set({ pathParams: params }),
  setRequestBody: (body) => set({ requestBody: body }),

  sendRequest: async (endpoints, mockServer) => {
    const { startRequest, setResponse } = useResponseStore.getState();
    const requestState = { ...get(), endpoints, mockServer };

    const endpoint = requestState.selectedNavItem;
    const { error, request } = buildRequestDetails(endpoint, requestState);
    if (error) {
      alert(error);
      return;
    }

    startRequest();
    const result = await executeProxyRequest(request);
    setResponse(result);
  },
}));
