import yaml from "js-yaml";
import axios from "axios";
import * as websocketService from "../../api/websocketService";
import { updateOperation, getSessionSpec } from "../../api/validationService";
import { implementationAPI } from "../../api/implementationAPI";
import { remediationAPI } from "../../api/remediationAPI";

const initialYamlSpec = `openapi: 3.0.4
info:
  title: Swagger Petstore - OpenAPI 3.0
  description: |-
    This is a sample Pet Store Server based on the OpenAPI 3.0 specification.  You can find out more about Swagger at [https://swagger.io](https://swagger.io). In the third iteration of the pet store, we'veswitched to the design first approach! You can now help us improve the API whether it's by making changes to the definition itself or to the code. That way, with time, we can improve the API in general, and expose some of the new features in OAS3.
    Some useful links: - [The Pet Store repository](https://github.com/swagger-api/swagger-petstore) - [The source API definition for the Pet Store](https://github.com/swagger-api/swagger-petstore/blob/master/src/main/resources/openapi.yaml)
  termsOfService: https://swagger.io/terms/
  contact:
    email: apiteam@swagger.io
  license:
    name: Apache 2.0
    url: https://www.apache.org/licenses/LICENSE-2.0.html
  version: 1.0.27
externalDocs:
  description: Find out more about Swagger
  url: https://swagger.io
servers:
  - url: /api/v3
tags:
  - name: pet
    description: Everything about your Pets
    externalDocs:
      description: Find out more
      url: https://swagger.io
  - name: store
    description: Access to Petstore orders
    externalDocs:
      description: Find out more about our store
      url: https://swagger.io
  - name: user
    description: Operations about user
`;

const initialJsonObject = yaml.load(initialYamlSpec);
const initialJsonSpec = JSON.stringify(initialJsonObject, null, 2);

export const coreSlice = (set, get) => ({
  // --- STATE ---
  specText: initialJsonSpec,
  sessionId: null,
  projectId: null,
  format: "json",
  activeRightPanelTab: "validation",
  skipNextValidation: false,

  // Implementation code state
  implementationCode: null,
  isFetchingImplementation: false,
  implementationError: null,

  // Remediation state
  suggestedFix: null,
  isSuggestingFix: false,
  suggestFixError: null,

  // --- ACTIONS ---
  setProjectId: (projectId) => set({ projectId }),

  setActiveRightPanelTab: (tabName) => set({ activeRightPanelTab: tabName }),

  setSkipNextValidation: (skip) => set({ skipNextValidation: skip }),

  connectWebSocket: () => {
    const handleMessage = (message) => {
      console.log("Broadcast message from server:", message);
    };
    websocketService.connect(handleMessage);
  },

  setSpecText: (newSpecText) => {
    let specToStore = newSpecText;
    let isJson = true;
    try {
      JSON.parse(newSpecText);
    } catch (e) {
      isJson = false;
    }

    if (!isJson) {
      try {
        const jsonObject = yaml.load(newSpecText);
        specToStore = JSON.stringify(jsonObject, null, 2);
      } catch (e) {
        console.error("Invalid YAML input:", e);
        set(() => ({ specText: newSpecText }));
        return;
      }
    }

    set(() => ({ specText: specToStore }));
  },

  createSession: async () => {
    try {
      const requestBody = { specText: get().specText };
      const response = await axios.post(
        "http://localhost:8080/api/v1/sessions",
        requestBody,
        { headers: { "Content-Type": "application/json" } },
      );
      const newSessionId = response.data.sessionId;
      set({ sessionId: newSessionId });
      console.log("Session created with ID:", newSessionId);
      return newSessionId;
    } catch (error) {
      console.error("Failed to create session:", error);
      throw error;
    }
  },

  convertToYAML: () => set({ format: "yaml" }),
  convertToJSON: () => set({ format: "json" }),

  updateOperationDetails: async (endpoint, formData) => {
    const state = get();
    if (!state.sessionId || !endpoint) return;

    const updateRequest = {
      path: endpoint.path,
      method: endpoint.method,
      summary: formData.summary,
      description: formData.description,
    };

    try {
      const result = await updateOperation(state.sessionId, updateRequest);
      if (result.success) {
        const specResult = await getSessionSpec(state.sessionId);
        if (specResult.success) {
          state.setSpecText(specResult.data);
        }
        return { success: true, message: "Operation updated successfully!" };
      } else {
        return { success: false, error: result.error };
      }
    } catch (error) {
      console.error("Error updating operation:", error);
      return { success: false, error: "Failed to update operation" };
    }
  },

  fetchImplementation: async (projectId, operationId) => {
    if (!projectId || !operationId) return;

    set({ isFetchingImplementation: true, implementationError: null });
    try {
      const implementation = await implementationAPI.getImplementation(
        projectId,
        operationId,
      );
      set({
        implementationCode: implementation,
        isFetchingImplementation: false,
      });
    } catch (error) {
      const errorMessage =
        error.response?.data?.message ||
        "Failed to fetch implementation. Is the repository linked and indexed?";
      set({
        isFetchingImplementation: false,
        implementationError: errorMessage,
        implementationCode: null,
      });
    }
  },

  suggestCodeFix: async ({ vulnerableCode, language, vulnerabilityType }) => {
    set({ isSuggestingFix: true, suggestFixError: null, suggestedFix: null });
    try {
      const result = await remediationAPI.suggestFix({
        vulnerableCode,
        language,
        vulnerabilityType,
      });
      set({
        isSuggestingFix: false,
        suggestedFix: result.suggestedFix,
      });
      return { success: true, data: result.suggestedFix };
    } catch (error) {
      const errorMessage =
        error.response?.data?.message || "AI failed to generate a fix.";
      set({ isSuggestingFix: false, suggestFixError: errorMessage });
      return { success: false, error: errorMessage };
    }
  },
});
