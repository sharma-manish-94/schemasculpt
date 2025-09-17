import React from "react";
import Editor from "@monaco-editor/react";
import { useSpecStore } from "../../../store/specStore";
import { useRequestStore } from "../../../store/requestStore";
import { useResponseStore } from "../../../store/responseStore";
import OperationEditorForm from "./OperationEditorForm";

function AILabPanel() {
  // Get state from the main store
  const { isLoading, setIsLoading, setActiveTab } = useSpecStore();

  // Get state and actions from the request store for building the request
  const {
    endpoints,
    selectedNavItem,
    serverTarget,
    setServerTarget,
    customServerUrl,
    setCustomServerUrl,
    mockServer,
    startMockServer,
    refreshMockServer,
    pathParams,
    setPathParams,
    sendRequest,
    requestBody,
    setRequestBody,
  } = useRequestStore();

  // Get state from the response store for displaying the result
  const { apiResponse, isApiRequestLoading } = useResponseStore();

  const selectedEndpoint = selectedNavItem;
  const pathParameters =
    selectedEndpoint?.details.parameters?.filter((p) => p.in === "path") || [];
  const hasRequestBody = !!selectedEndpoint?.details.requestBody;

  const handlePathParamChange = (name, value) => {
    // We create a new object from the existing state to ensure re-renders
    const newPathParams = { ...pathParams, [name]: value };
    setPathParams(newPathParams);
  };

  const handleStartServerClick = async () => {
    setIsLoading(true); // 1. Set loading state in the main store
    const success = await startMockServer(); // 2. Call the action in the request store
    if (success) {
      setActiveTab("api_lab"); // 3. If successful, change tab state in the main store
    }
    setIsLoading(false); // 4. Set loading to false in the main store
  };

  const handleSendClick = () => {
    sendRequest(endpoints, mockServer);
  };

  return (
    <div className="api-lab-container">
      <div className="form-group">
        <label>Target Server</label>
        <div className="radio-group">
          <input
            type="radio"
            id="mock-server"
            name="server-target"
            value="mock"
            checked={serverTarget === "mock"}
            onChange={() => setServerTarget("mock")}
          />
          <label htmlFor="mock-server">AI Mock Server</label>
          <input
            type="radio"
            id="custom-server"
            name="server-target"
            value="custom"
            checked={serverTarget === "custom"}
            onChange={() => setServerTarget("custom")}
          />
          <label htmlFor="custom-server">Custom Server</label>
        </div>
        {serverTarget === "custom" && (
          <input
            type="text"
            className="text-input"
            placeholder="Enter your base URL, e.g., http://localhost:9090"
            value={customServerUrl}
            onChange={(e) => setCustomServerUrl(e.target.value)}
          />
        )}
        {serverTarget === "mock" && !mockServer.active && (
          <button
            className="start-mock-button"
            onClick={handleStartServerClick}
            disabled={isLoading}
          >
            {isLoading ? "Starting..." : "Start AI Mock Server"}
          </button>
        )}
        {serverTarget === "mock" && mockServer.active && (
          <div>
            <div className="mock-url-container">
              <input
                type="text"
                className="text-input"
                readOnly
                value={mockServer.url}
              />
              <button
                className="refresh-button"
                onClick={refreshMockServer}
                title="Update the mock server with the latest spec from the editor"
              >
                🔄 Refresh
              </button>
            </div>
          </div>
        )}
      </div>
      <hr className="divider" />
      <OperationEditorForm endpoint={selectedEndpoint} />
      <hr className="divider" />
      {selectedEndpoint && (
        <>
          <div className="request-builder">
            <h4>Request</h4>
            {pathParameters.map((param) => (
              <div className="form-group" key={param.name}>
                <label htmlFor={`param-${param.name}`}>
                  {param.name} <span className="param-location">(path)</span>
                </label>
                <input
                  type="text"
                  id={`param-${param.name}`}
                  className="text-input"
                  placeholder={param.description || ""}
                  value={pathParams[param.name] || ""}
                  onChange={(e) =>
                    handlePathParamChange(param.name, e.target.value)
                  }
                />
              </div>
            ))}
            {hasRequestBody && (
              <div className="form-group">
                <label>
                  Body{" "}
                  <span className="param-location">(application/json)</span>
                </label>
                <div className="body-editor-wrapper">
                  <Editor
                    height="200px"
                    language="json"
                    theme="vs-dark"
                    value={requestBody}
                    onChange={(value) => setRequestBody(value || "")}
                    options={{
                      minimap: { enabled: false },
                      lineNumbers: "off",
                    }}
                  />
                </div>
              </div>
            )}
            <button
              className="send-request-button"
              onClick={handleSendClick}
              disabled={isApiRequestLoading}
            >
              {isApiRequestLoading ? "Sending..." : "Send Request"}
            </button>
          </div>

          <div className="response-viewer">
            <h4>Response</h4>
            {isApiRequestLoading ? (
              <p className="loading-text">Waiting for response...</p>
            ) : apiResponse ? (
              <pre
                className={
                  apiResponse.success ? "response-success" : "response-error"
                }
              >
                {JSON.stringify(apiResponse.data || apiResponse.error, null, 2)}
              </pre>
            ) : (
              <p className="no-errors">Response will be displayed here.</p>
            )}
          </div>
        </>
      )}
    </div>
  );
}

export default AILabPanel;
