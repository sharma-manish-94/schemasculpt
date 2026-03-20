import React, { useState, useEffect } from "react";
import { useSpecStore } from "../../../store/specStore";
import Button from "../../../components/ui/Button";
import LoadingSpinner from "../../../components/ui/LoadingSpinner";
import ErrorMessage from "../../../components/ui/ErrorMessage";
import "../ai-features.css";

/**
 * API Lab - Testing & Mocking Suite
 *
 * Features:
 * 1. Mock Server Management - Start/stop mock servers with AI-generated data
 * 2. Test Case Generation - Generate happy/sad path tests
 * 3. Mock Data Variations - Generate diverse test data
 * 4. Test Runner - Execute tests against mock or real servers
 */
function APILab() {
  const { specText } = useSpecStore();

  const [activeTab, setActiveTab] = useState("mock-server");
  const [mockServer, setMockServer] = useState(null);
  const [testCases, setTestCases] = useState(null);
  const [mockData, setMockData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Mock Server state
  const [mockServerConfig, setMockServerConfig] = useState({
    useAI: true,
    responseDelay: 0,
    errorRate: 0.0,
    responseVariety: 3,
  });

  // Test Generation state
  const [selectedEndpoint, setSelectedEndpoint] = useState({
    path: "",
    method: "GET",
  });
  const [availableEndpoints, setAvailableEndpoints] = useState([]);
  const [includeAITests, setIncludeAITests] = useState(true);

  // Mock Data Generation state
  const [mockDataConfig, setMockDataConfig] = useState({
    path: "",
    method: "GET",
    responseCode: "200",
    variationCount: 3,
    useAI: true,
  });

  // Parse spec to get available endpoints
  useEffect(() => {
    if (specText) {
      try {
        const spec = JSON.parse(specText);
        const endpoints = [];

        Object.keys(spec.paths || {}).forEach((path) => {
          Object.keys(spec.paths[path]).forEach((method) => {
            if (["get", "post", "put", "patch", "delete"].includes(method)) {
              endpoints.push({
                path,
                method: method.toUpperCase(),
                summary: spec.paths[path][method].summary || "",
                operationId: spec.paths[path][method].operationId || "",
              });
            }
          });
        });

        setAvailableEndpoints(endpoints);

        if (endpoints.length > 0 && !selectedEndpoint.path) {
          setSelectedEndpoint({
            path: endpoints[0].path,
            method: endpoints[0].method,
          });
        }
      } catch (e) {
        console.error("Failed to parse spec:", e);
      }
    }
  }, [specText]);

  const startMockServer = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch("http://localhost:8000/ai/mock/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          spec_text: specText,
          host: "localhost",
          port: 8001,
          use_ai_responses: mockServerConfig.useAI,
          response_delay_ms: mockServerConfig.responseDelay,
          error_rate: mockServerConfig.errorRate,
          response_variety: mockServerConfig.responseVariety,
        }),
      });

      if (!response.ok) {
        throw new Error(`Failed to start mock server: ${response.statusText}`);
      }

      const data = await response.json();
      setMockServer(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const refreshMockServer = async () => {
    if (!mockServer) return;

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `http://localhost:8000/ai/mock/${mockServer.mock_id}`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            spec_text: specText,
            host: mockServer.host,
            port: mockServer.port,
            use_ai_responses: mockServerConfig.useAI,
            response_delay_ms: mockServerConfig.responseDelay,
            error_rate: mockServerConfig.errorRate,
          }),
        },
      );

      if (!response.ok) {
        throw new Error(
          `Failed to refresh mock server: ${response.statusText}`,
        );
      }

      const data = await response.json();
      setMockServer(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const generateTestCases = async () => {
    if (!selectedEndpoint.path) {
      setError("Please select an endpoint");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch("http://localhost:8000/ai/tests/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          spec_text: specText,
          path: selectedEndpoint.path,
          method: selectedEndpoint.method,
          include_ai_tests: includeAITests,
        }),
      });

      if (!response.ok) {
        throw new Error(
          `Failed to generate test cases: ${response.statusText}`,
        );
      }

      const data = await response.json();
      setTestCases(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const generateMockDataVariations = async () => {
    if (!mockDataConfig.path) {
      setError("Please select an endpoint");
      return;
    }

    setLoading(true);
    setError(null);

    // Create AbortController for 120 second timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 120000);

    try {
      const response = await fetch(
        "http://localhost:8000/ai/mock/generate-variations",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            spec_text: specText,
            path: mockDataConfig.path,
            method: mockDataConfig.method.toLowerCase(),
            response_code: mockDataConfig.responseCode,
            count: mockDataConfig.variationCount,
          }),
          signal: controller.signal,
        },
      );

      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new Error(`Failed to generate mock data: ${response.statusText}`);
      }

      const data = await response.json();
      setMockData(data.variations);
    } catch (err) {
      if (err.name === "AbortError") {
        setError("Request timed out after 120 seconds. Please try again.");
      } else {
        setError(err.message);
      }
    } finally {
      clearTimeout(timeoutId);
      setLoading(false);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
  };

  return (
    <div className="api-lab-container">
      <div className="api-lab-header">
        <h2>🧪 API Lab</h2>
        <p>Testing & Mocking Suite for your OpenAPI specification</p>
      </div>

      {/* Tab Navigation */}
      <div className="api-lab-tabs">
        <button
          className={`tab-button ${
            activeTab === "mock-server" ? "active" : ""
          }`}
          onClick={() => setActiveTab("mock-server")}
        >
          Mock Server
        </button>
        <button
          className={`tab-button ${activeTab === "test-cases" ? "active" : ""}`}
          onClick={() => setActiveTab("test-cases")}
        >
          Test Cases
        </button>
        <button
          className={`tab-button ${activeTab === "mock-data" ? "active" : ""}`}
          onClick={() => setActiveTab("mock-data")}
        >
          Mock Data
        </button>
      </div>

      {/* Error Display */}
      {error && (
        <ErrorMessage message={error} onDismiss={() => setError(null)} />
      )}

      {/* Mock Server Tab */}
      {activeTab === "mock-server" && (
        <div className="tab-content">
          <h3>AI-Powered Mock Server</h3>
          <p>
            Start a mock server that returns realistic, AI-generated responses
          </p>

          <div className="config-section">
            <h4>Configuration</h4>
            <div className="config-options">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={mockServerConfig.useAI}
                  onChange={(e) =>
                    setMockServerConfig({
                      ...mockServerConfig,
                      useAI: e.target.checked,
                    })
                  }
                />
                Use AI for realistic responses
              </label>

              <div className="config-row">
                <label>
                  Response Delay (ms):
                  <input
                    type="number"
                    value={mockServerConfig.responseDelay}
                    onChange={(e) =>
                      setMockServerConfig({
                        ...mockServerConfig,
                        responseDelay: parseInt(e.target.value) || 0,
                      })
                    }
                    min="0"
                    max="5000"
                  />
                </label>
              </div>

              <div className="config-row">
                <label>
                  Error Rate (0.0 - 1.0):
                  <input
                    type="number"
                    step="0.1"
                    value={mockServerConfig.errorRate}
                    onChange={(e) =>
                      setMockServerConfig({
                        ...mockServerConfig,
                        errorRate: parseFloat(e.target.value) || 0,
                      })
                    }
                    min="0"
                    max="1"
                  />
                </label>
              </div>

              <div className="config-row">
                <label>
                  Response Variety (1-10):
                  <input
                    type="number"
                    value={mockServerConfig.responseVariety}
                    onChange={(e) =>
                      setMockServerConfig({
                        ...mockServerConfig,
                        responseVariety: parseInt(e.target.value) || 3,
                      })
                    }
                    min="1"
                    max="10"
                  />
                </label>
              </div>
            </div>
          </div>

          <div className="action-buttons">
            <Button onClick={startMockServer} disabled={loading || !specText}>
              {loading ? (
                <LoadingSpinner size="small" />
              ) : mockServer ? (
                "Restart Mock Server"
              ) : (
                "Start Mock Server"
              )}
            </Button>

            {mockServer && (
              <Button
                onClick={refreshMockServer}
                disabled={loading}
                variant="secondary"
              >
                Refresh Configuration
              </Button>
            )}
          </div>

          {mockServer && (
            <div className="mock-server-info">
              <h4>✅ Mock Server Running</h4>
              <div className="info-grid">
                <div className="info-item">
                  <strong>Base URL:</strong>
                  <code>{`http://${mockServer.host}:${mockServer.port}${mockServer.base_url}`}</code>
                  <button
                    onClick={() =>
                      copyToClipboard(
                        `http://${mockServer.host}:${mockServer.port}${mockServer.base_url}`,
                      )
                    }
                  >
                    📋 Copy
                  </button>
                </div>
                <div className="info-item">
                  <strong>Available Endpoints:</strong>{" "}
                  {mockServer.total_endpoints}
                </div>
                <div className="info-item">
                  <strong>Status:</strong>{" "}
                  <span className="status-badge">{mockServer.status}</span>
                </div>
              </div>

              <div className="endpoints-list">
                <h5>Available Endpoints:</h5>
                <ul>
                  {mockServer.available_endpoints?.map((endpoint, idx) => (
                    <li key={idx}>
                      <code>{endpoint}</code>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Test Cases Tab */}
      {activeTab === "test-cases" && (
        <div className="tab-content">
          <h3>AI-Generated Test Cases</h3>
          <p>
            Generate comprehensive test scenarios including happy paths, sad
            paths, and edge cases
          </p>

          <div className="config-section">
            <h4>Select Endpoint</h4>
            <select
              value={`${selectedEndpoint.method}:${selectedEndpoint.path}`}
              onChange={(e) => {
                const [method, ...pathParts] = e.target.value.split(":");
                setSelectedEndpoint({ method, path: pathParts.join(":") });
              }}
              className="endpoint-selector"
            >
              {availableEndpoints.map((ep, idx) => (
                <option key={idx} value={`${ep.method}:${ep.path}`}>
                  {ep.method} {ep.path} {ep.summary && `- ${ep.summary}`}
                </option>
              ))}
            </select>

            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={includeAITests}
                onChange={(e) => setIncludeAITests(e.target.checked)}
              />
              Include AI-generated advanced test scenarios
            </label>
          </div>

          <div className="action-buttons">
            <Button
              onClick={generateTestCases}
              disabled={loading || !specText || !selectedEndpoint.path}
            >
              {loading ? (
                <LoadingSpinner size="small" />
              ) : (
                "Generate Test Cases"
              )}
            </Button>
          </div>

          {testCases && (
            <div className="test-cases-results">
              <h4>📊 Generated Test Cases</h4>
              <div className="test-summary">
                <span className="summary-item">
                  Total: {testCases.total_tests}
                </span>
                <span className="summary-item happy">
                  Happy Path: {testCases.happy_path_tests?.length || 0}
                </span>
                <span className="summary-item sad">
                  Sad Path: {testCases.sad_path_tests?.length || 0}
                </span>
                <span className="summary-item edge">
                  Edge Cases: {testCases.edge_case_tests?.length || 0}
                </span>
                {testCases.ai_generated_tests && (
                  <span className="summary-item ai">
                    AI Tests: {testCases.ai_generated_tests.length}
                  </span>
                )}
              </div>

              <TestCasesList
                tests={testCases.happy_path_tests}
                title="✅ Happy Path Tests"
                type="happy"
              />
              <TestCasesList
                tests={testCases.sad_path_tests}
                title="❌ Sad Path Tests"
                type="sad"
              />
              <TestCasesList
                tests={testCases.edge_case_tests}
                title="⚠️ Edge Case Tests"
                type="edge"
              />
              {testCases.ai_generated_tests &&
                testCases.ai_generated_tests.length > 0 && (
                  <TestCasesList
                    tests={testCases.ai_generated_tests}
                    title="🤖 AI-Generated Advanced Tests"
                    type="ai"
                  />
                )}
            </div>
          )}
        </div>
      )}

      {/* Mock Data Tab */}
      {activeTab === "mock-data" && (
        <div className="tab-content">
          <h3>Mock Data Variations</h3>
          <p>Generate multiple variations of realistic mock data for testing</p>

          <div className="config-section">
            <h4>Configure Mock Data Generation</h4>

            <div className="config-row">
              <label>
                Endpoint:
                <select
                  value={`${mockDataConfig.method}:${mockDataConfig.path}`}
                  onChange={(e) => {
                    const [method, ...pathParts] = e.target.value.split(":");
                    setMockDataConfig({
                      ...mockDataConfig,
                      method,
                      path: pathParts.join(":"),
                    });
                  }}
                  className="endpoint-selector"
                >
                  <option value=":">Select an endpoint...</option>
                  {availableEndpoints.map((ep, idx) => (
                    <option key={idx} value={`${ep.method}:${ep.path}`}>
                      {ep.method} {ep.path}
                    </option>
                  ))}
                </select>
              </label>
            </div>

            <div className="config-row">
              <label>
                Response Code:
                <input
                  type="text"
                  value={mockDataConfig.responseCode}
                  onChange={(e) =>
                    setMockDataConfig({
                      ...mockDataConfig,
                      responseCode: e.target.value,
                    })
                  }
                  placeholder="200"
                />
              </label>
            </div>

            <div className="config-row">
              <label>
                Number of Variations:
                <input
                  type="number"
                  value={mockDataConfig.variationCount}
                  onChange={(e) =>
                    setMockDataConfig({
                      ...mockDataConfig,
                      variationCount: parseInt(e.target.value) || 3,
                    })
                  }
                  min="1"
                  max="10"
                />
              </label>
            </div>

            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={mockDataConfig.useAI}
                onChange={(e) =>
                  setMockDataConfig({
                    ...mockDataConfig,
                    useAI: e.target.checked,
                  })
                }
              />
              Use AI for generation (first variation only)
            </label>
          </div>

          <div className="action-buttons">
            <Button
              onClick={generateMockDataVariations}
              disabled={loading || !specText || !mockDataConfig.path}
            >
              {loading ? <LoadingSpinner size="small" /> : "Generate Mock Data"}
            </Button>
          </div>

          {mockData && mockData.length > 0 && (
            <div className="mock-data-results">
              <h4>📦 Generated Mock Data ({mockData.length} variations)</h4>
              <div className="mock-data-grid">
                {mockData.map((data, idx) => (
                  <div key={idx} className="mock-data-card">
                    <div className="card-header">
                      <h5>Variation {idx + 1}</h5>
                      <button
                        onClick={() =>
                          copyToClipboard(JSON.stringify(data, null, 2))
                        }
                      >
                        📋 Copy JSON
                      </button>
                    </div>
                    <pre className="mock-data-preview">
                      {JSON.stringify(data, null, 2)}
                    </pre>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/**
 * Test Cases List Component
 */
function TestCasesList({ tests, title, type }) {
  const [expanded, setExpanded] = useState(true);

  if (!tests || tests.length === 0) return null;

  return (
    <div className={`test-cases-section ${type}`}>
      <div className="section-header" onClick={() => setExpanded(!expanded)}>
        <h5>
          {title} ({tests.length})
        </h5>
        <span className="expand-icon">{expanded ? "▼" : "▶"}</span>
      </div>

      {expanded && (
        <div className="test-cases-list">
          {tests.map((test, idx) => (
            <div key={idx} className="test-case-card">
              <div className="test-case-header">
                <h6>{test.name}</h6>
                <span className={`test-type-badge ${test.type}`}>
                  {test.type}
                </span>
              </div>

              <p className="test-description">{test.description}</p>

              <div className="test-details">
                <div className="detail-row">
                  <strong>Method:</strong> <code>{test.method}</code>
                </div>
                <div className="detail-row">
                  <strong>Path:</strong> <code>{test.path}</code>
                </div>
                <div className="detail-row">
                  <strong>Expected Status:</strong>{" "}
                  <span className="status-code">{test.expected_status}</span>
                </div>

                {test.request_body &&
                  Object.keys(test.request_body).length > 0 && (
                    <div className="detail-row">
                      <strong>Request Body:</strong>
                      <pre>{JSON.stringify(test.request_body, null, 2)}</pre>
                    </div>
                  )}

                {test.query_params &&
                  Object.keys(test.query_params).length > 0 && (
                    <div className="detail-row">
                      <strong>Query Params:</strong>
                      <code>{JSON.stringify(test.query_params)}</code>
                    </div>
                  )}

                {test.headers && Object.keys(test.headers).length > 0 && (
                  <div className="detail-row">
                    <strong>Headers:</strong>
                    <code>{JSON.stringify(test.headers)}</code>
                  </div>
                )}

                {test.assertions && test.assertions.length > 0 && (
                  <div className="detail-row">
                    <strong>Assertions:</strong>
                    <ul className="assertions-list">
                      {test.assertions.map((assertion, i) => (
                        <li key={i}>{assertion}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default APILab;
