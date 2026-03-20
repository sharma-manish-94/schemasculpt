import React, {
  useMemo,
  useCallback,
  useRef,
  useEffect,
  useState,
} from "react";
import SwaggerUI from "swagger-ui-react";
import { useSpecStore } from "../../../store/specStore";

const EXPLORER_TABS = {
  TRY_IT: "try-it",
  MOCK_DATA: "mock-data",
  TEST_CASES: "test-cases",
};

function MockServerControls() {
  const {
    isLoading,
    setIsLoading,
    mockServer,
    startMockServer,
    refreshMockServer,
    serverTarget,
    setServerTarget,
    customServerUrl,
    setCustomServerUrl,
  } = useSpecStore();

  const handleStartServerClick = async () => {
    setIsLoading(true);
    await startMockServer();
    setIsLoading(false);
  };

  return (
    <div className="mock-server-controls">
      <div className="server-selection">
        <h4>API Server</h4>
        <div className="radio-group">
          <label className="radio-option">
            <input
              type="radio"
              name="server-target"
              value="spec"
              checked={serverTarget === "spec"}
              onChange={() => setServerTarget("spec")}
            />
            <span>Use Spec Servers</span>
          </label>
          <label className="radio-option">
            <input
              type="radio"
              name="server-target"
              value="mock"
              checked={serverTarget === "mock"}
              onChange={() => setServerTarget("mock")}
            />
            <span>AI Mock Server</span>
          </label>
          <label className="radio-option">
            <input
              type="radio"
              name="server-target"
              value="custom"
              checked={serverTarget === "custom"}
              onChange={() => setServerTarget("custom")}
            />
            <span>Custom Server</span>
          </label>
        </div>

        {serverTarget === "custom" && (
          <div className="custom-server-input">
            <input
              type="text"
              className="text-input"
              placeholder="Enter your base URL, e.g., http://localhost:9090"
              value={customServerUrl}
              onChange={(e) => setCustomServerUrl(e.target.value)}
            />
          </div>
        )}

        {serverTarget === "mock" && !mockServer.active && (
          <div className="mock-server-start">
            <button
              className="start-mock-button"
              onClick={handleStartServerClick}
              disabled={isLoading}
            >
              {isLoading ? "Starting..." : "🚀 Start AI Mock Server"}
            </button>
          </div>
        )}

        {serverTarget === "mock" && mockServer.active && (
          <div className="mock-server-active">
            <div className="mock-status">
              <span className="status-indicator active">●</span>
              <span>Mock Server Active</span>
            </div>
            <div className="mock-url-display">
              <input
                type="text"
                className="text-input mock-url"
                readOnly
                value={mockServer.url}
              />
              <button
                className="refresh-button"
                onClick={refreshMockServer}
                title="Update the mock server with the latest spec from the editor"
              >
                🔄
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function MockDataTab() {
  const { specText } = useSpecStore();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [mockData, setMockData] = useState([]);
  const [selectedPath, setSelectedPath] = useState("");
  const [selectedMethod, setSelectedMethod] = useState("GET");
  const [responseCode, setResponseCode] = useState("200");
  const [variationCount, setVariationCount] = useState(3);
  const [availableEndpoints, setAvailableEndpoints] = useState([]);

  // Parse spec to get endpoints
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
              });
            }
          });
        });
        setAvailableEndpoints(endpoints);
        if (endpoints.length > 0 && !selectedPath) {
          setSelectedPath(endpoints[0].path);
          setSelectedMethod(endpoints[0].method);
        }
      } catch (e) {
        console.error("Failed to parse spec:", e);
      }
    }
  }, [specText]);

  const generateMockData = async () => {
    setLoading(true);
    setError(null);

    // Create AbortController for 120 second timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 120000);

    try {
      const response = await fetch(
        "http://localhost:8000/mock/generate-variations",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            spec_text: specText,
            path: selectedPath,
            method: selectedMethod.toLowerCase(),
            response_code: responseCode,
            count: variationCount,
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
    <div className="mock-data-tab">
      <div className="tab-header">
        <h3>🎲 Mock Data Generator</h3>
        <p>Generate realistic, AI-powered mock data variations for testing</p>
      </div>

      <div className="mock-config">
        <div className="config-row">
          <label>
            Endpoint:
            <select
              value={`${selectedMethod}:${selectedPath}`}
              onChange={(e) => {
                const [method, ...pathParts] = e.target.value.split(":");
                setSelectedMethod(method);
                setSelectedPath(pathParts.join(":"));
              }}
              className="select-input"
            >
              {availableEndpoints.map((ep, idx) => (
                <option key={idx} value={`${ep.method}:${ep.path}`}>
                  {ep.method} {ep.path} {ep.summary && `- ${ep.summary}`}
                </option>
              ))}
            </select>
          </label>
        </div>

        <div className="config-row-group">
          <label>
            Response Code:
            <input
              type="text"
              value={responseCode}
              onChange={(e) => setResponseCode(e.target.value)}
              className="text-input small"
            />
          </label>

          <label>
            Variations:
            <input
              type="number"
              value={variationCount}
              onChange={(e) => setVariationCount(parseInt(e.target.value) || 3)}
              min="1"
              max="10"
              className="text-input small"
            />
          </label>
        </div>

        <button
          onClick={generateMockData}
          disabled={loading || !selectedPath}
          className="generate-button"
        >
          {loading ? "Generating..." : "✨ Generate Mock Data"}
        </button>
      </div>

      {error && <div className="error-message">❌ {error}</div>}

      {mockData && mockData.length > 0 && (
        <div className="mock-results">
          <h4>📦 Generated Variations ({mockData.length})</h4>
          <div className="mock-grid">
            {mockData.map((data, idx) => (
              <div key={idx} className="mock-card">
                <div className="card-header">
                  <span>Variation {idx + 1}</span>
                  <button
                    onClick={() =>
                      copyToClipboard(JSON.stringify(data, null, 2))
                    }
                    className="copy-btn"
                  >
                    📋 Copy
                  </button>
                </div>
                <pre className="mock-preview">
                  {JSON.stringify(data, null, 2)}
                </pre>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function TestCasesTab() {
  const { specText } = useSpecStore();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [testCases, setTestCases] = useState(null);
  const [selectedPath, setSelectedPath] = useState("");
  const [selectedMethod, setSelectedMethod] = useState("GET");
  const [includeAITests, setIncludeAITests] = useState(true);
  const [availableEndpoints, setAvailableEndpoints] = useState([]);

  // Parse spec to get endpoints
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
              });
            }
          });
        });
        setAvailableEndpoints(endpoints);
        if (endpoints.length > 0 && !selectedPath) {
          setSelectedPath(endpoints[0].path);
          setSelectedMethod(endpoints[0].method);
        }
      } catch (e) {
        console.error("Failed to parse spec:", e);
      }
    }
  }, [specText]);

  const generateTestCases = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch("http://localhost:8000/tests/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          spec_text: specText,
          path: selectedPath,
          method: selectedMethod,
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

  return (
    <div className="test-cases-tab">
      <div className="tab-header">
        <h3>🧪 Test Case Generator</h3>
        <p>
          Generate comprehensive test scenarios including happy paths, sad
          paths, and edge cases
        </p>
      </div>

      <div className="test-config">
        <div className="config-row">
          <label>
            Endpoint:
            <select
              value={`${selectedMethod}:${selectedPath}`}
              onChange={(e) => {
                const [method, ...pathParts] = e.target.value.split(":");
                setSelectedMethod(method);
                setSelectedPath(pathParts.join(":"));
              }}
              className="select-input"
            >
              {availableEndpoints.map((ep, idx) => (
                <option key={idx} value={`${ep.method}:${ep.path}`}>
                  {ep.method} {ep.path} {ep.summary && `- ${ep.summary}`}
                </option>
              ))}
            </select>
          </label>
        </div>

        <div className="checkbox-row">
          <label>
            <input
              type="checkbox"
              checked={includeAITests}
              onChange={(e) => setIncludeAITests(e.target.checked)}
            />
            Include AI-generated advanced test scenarios
          </label>
        </div>

        <button
          onClick={generateTestCases}
          disabled={loading || !selectedPath}
          className="generate-button"
        >
          {loading ? "Generating..." : "🔬 Generate Test Cases"}
        </button>
      </div>

      {error && <div className="error-message">❌ {error}</div>}

      {testCases && (
        <div className="test-results">
          <div className="test-summary">
            <div className="summary-badge">Total: {testCases.total_tests}</div>
            <div className="summary-badge happy">
              ✅ Happy: {testCases.happy_path_tests?.length || 0}
            </div>
            <div className="summary-badge sad">
              ❌ Sad: {testCases.sad_path_tests?.length || 0}
            </div>
            <div className="summary-badge edge">
              ⚠️ Edge: {testCases.edge_case_tests?.length || 0}
            </div>
            {testCases.ai_generated_tests &&
              testCases.ai_generated_tests.length > 0 && (
                <div className="summary-badge ai">
                  🤖 AI: {testCases.ai_generated_tests.length}
                </div>
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
  );
}

function TestCasesList({ tests, title, type }) {
  const [expanded, setExpanded] = useState(true);

  if (!tests || tests.length === 0) return null;

  return (
    <div className={`test-section ${type}`}>
      <div className="section-header" onClick={() => setExpanded(!expanded)}>
        <h4>
          {title} ({tests.length})
        </h4>
        <span className="expand-icon">{expanded ? "▼" : "▶"}</span>
      </div>

      {expanded && (
        <div className="test-list">
          {tests.map((test, idx) => (
            <div key={idx} className="test-card">
              <div className="test-header">
                <strong>{test.name}</strong>
                <span className={`test-badge ${test.type}`}>{test.type}</span>
              </div>
              <p className="test-desc">{test.description}</p>
              <div className="test-details">
                <div>
                  <strong>Method:</strong> <code>{test.method}</code>
                </div>
                <div>
                  <strong>Expected:</strong>{" "}
                  <span className="status-code">{test.expected_status}</span>
                </div>
                {test.request_body &&
                  Object.keys(test.request_body).length > 0 && (
                    <div>
                      <strong>Body:</strong>
                      <pre>{JSON.stringify(test.request_body, null, 2)}</pre>
                    </div>
                  )}
                {test.assertions && test.assertions.length > 0 && (
                  <div>
                    <strong>Assertions:</strong>
                    <ul>
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

function EnhancedSwaggerUI() {
  const {
    specText,
    mockServer,
    serverTarget,
    customServerUrl,
    selectedNavItem,
  } = useSpecStore();

  const [activeTab, setActiveTab] = useState(EXPLORER_TABS.TRY_IT);

  // Ref to store Swagger UI system object for programmatic control
  const swaggerSystemRef = useRef(null);

  // Parse specText for SwaggerUI
  const parsedSpec = useMemo(() => {
    try {
      return JSON.parse(specText);
    } catch (error) {
      console.error("Failed to parse spec for SwaggerUI:", error);
      return null;
    }
  }, [specText]);

  // Extract original server URLs from spec
  const originalServers = useMemo(() => {
    if (!parsedSpec?.servers) return [];
    return parsedSpec.servers.map((server) => server.url);
  }, [parsedSpec]);

  // Request interceptor to handle different server targets
  const requestInterceptor = useCallback(
    (req) => {
      let targetBaseUrl = null;

      switch (serverTarget) {
        case "mock":
          if (mockServer.active) {
            targetBaseUrl = mockServer.url;
            req.headers["X-Mock-Server"] = "true";
          }
          break;
        case "custom":
          if (customServerUrl) {
            targetBaseUrl = customServerUrl.replace(/\/$/, "");
          }
          break;
        case "spec":
        default:
          break;
      }

      if (targetBaseUrl) {
        try {
          const url = new URL(req.url);
          let path = url.pathname + url.search;

          // For mock server, remove any existing server base paths
          if (serverTarget === "mock" && originalServers.length > 0) {
            originalServers.forEach((serverUrl) => {
              try {
                const serverUrlObj = new URL(serverUrl, "http://dummy");
                if (path.startsWith(serverUrlObj.pathname)) {
                  path = path.substring(serverUrlObj.pathname.length);
                }
              } catch (e) {
                // If serverUrl is relative, just use it
                if (path.startsWith(serverUrl)) {
                  path = path.substring(serverUrl.length);
                }
              }
            });

            // Ensure path starts with /
            if (!path.startsWith("/")) {
              path = "/" + path;
            }
          }

          req.url = targetBaseUrl + path;
        } catch (error) {
          console.error("Error intercepting request:", error);
          // Fallback to simple replacement
          if (originalServers.length > 0) {
            originalServers.forEach((serverUrl) => {
              if (req.url.includes(serverUrl)) {
                req.url = req.url.replace(serverUrl, targetBaseUrl);
              }
            });
          }
        }
      }

      return req;
    },
    [serverTarget, mockServer, customServerUrl, originalServers],
  );

  // Response interceptor
  const responseInterceptor = useCallback(
    (response) => {
      if (serverTarget === "mock" && mockServer.active) {
        console.log("Response from mock server:", response);
      }
      return response;
    },
    [serverTarget, mockServer],
  );

  // Callback when Swagger UI finishes rendering
  const onComplete = useCallback((system) => {
    swaggerSystemRef.current = system;
  }, []);

  // Function to scroll to and highlight a specific operation
  const scrollToOperation = useCallback((path, method) => {
    setTimeout(() => {
      const tagButtons = document.querySelectorAll(
        ".opblock-tag-section .opblock-tag",
      );
      tagButtons.forEach((tagButton) => {
        const section = tagButton.closest(".opblock-tag-section");
        if (section && !section.classList.contains("is-open")) {
          tagButton.click();
        }
      });

      setTimeout(() => {
        const allOpBlocks = document.querySelectorAll(".opblock");
        for (const block of allOpBlocks) {
          const pathEl = block.querySelector(".opblock-summary-path");
          const methodEl = block.querySelector(".opblock-summary-method");

          if (pathEl && methodEl) {
            const blockPath = pathEl.textContent?.trim();
            const blockMethod = methodEl.textContent?.trim().toLowerCase();

            if (blockPath === path && blockMethod === method.toLowerCase()) {
              const summary = block.querySelector(".opblock-summary");
              if (summary && !block.classList.contains("is-open")) {
                summary.click();
              }

              block.scrollIntoView({
                behavior: "smooth",
                block: "start",
                inline: "nearest",
              });

              block.style.outline = "3px solid #0066cc";
              block.style.outlineOffset = "2px";
              setTimeout(() => {
                block.style.outline = "";
                block.style.outlineOffset = "";
              }, 3000);

              break;
            }
          }
        }
      }, 200);
    }, 100);
  }, []);

  // Effect to handle operation highlighting when selectedNavItem changes
  useEffect(() => {
    if (selectedNavItem && activeTab === EXPLORER_TABS.TRY_IT) {
      scrollToOperation(selectedNavItem.path, selectedNavItem.method);
    }
  }, [selectedNavItem, scrollToOperation, activeTab]);

  if (!parsedSpec) {
    return (
      <div className="swagger-ui-container">
        <MockServerControls />
        <div className="panel-content-placeholder">
          Invalid JSON - cannot display API documentation
        </div>
      </div>
    );
  }

  return (
    <div className="swagger-ui-container">
      <MockServerControls />

      {/* Tab Navigation */}
      <div className="explorer-tabs">
        <button
          className={`explorer-tab ${
            activeTab === EXPLORER_TABS.TRY_IT ? "active" : ""
          }`}
          onClick={() => setActiveTab(EXPLORER_TABS.TRY_IT)}
        >
          🔧 Try It
        </button>
        <button
          className={`explorer-tab ${
            activeTab === EXPLORER_TABS.MOCK_DATA ? "active" : ""
          }`}
          onClick={() => setActiveTab(EXPLORER_TABS.MOCK_DATA)}
        >
          🎲 Mock Data
        </button>
        <button
          className={`explorer-tab ${
            activeTab === EXPLORER_TABS.TEST_CASES ? "active" : ""
          }`}
          onClick={() => setActiveTab(EXPLORER_TABS.TEST_CASES)}
        >
          🧪 Test Cases
        </button>
      </div>

      {/* Tab Content */}
      <div className="explorer-content">
        {activeTab === EXPLORER_TABS.TRY_IT && (
          <div className="swagger-ui-wrapper">
            <SwaggerUI
              spec={parsedSpec}
              requestInterceptor={requestInterceptor}
              responseInterceptor={responseInterceptor}
              onComplete={onComplete}
              tryItOutEnabled={true}
              displayRequestDuration={true}
              filter={true}
              showExtensions={true}
              showCommonExtensions={true}
              docExpansion="none"
              deepLinking={true}
              defaultModelsExpandDepth={1}
              defaultModelExpandDepth={1}
            />
          </div>
        )}

        {activeTab === EXPLORER_TABS.MOCK_DATA && <MockDataTab />}
        {activeTab === EXPLORER_TABS.TEST_CASES && <TestCasesTab />}
      </div>
    </div>
  );
}

export default EnhancedSwaggerUI;
