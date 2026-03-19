import { useSpecStore } from "../../../store/specStore";
import React from "react";

function NavigationPanel() {
  const {
    endpoints,
    selectedNavItem,
    setSelectedNavItem,
    projectId,
    fetchImplementation,
    setActiveRightPanelTab,
  } = useSpecStore();

  const paths = endpoints.reduce((acc, ep) => {
    acc[ep.path] = [...(acc[ep.path] || []), ep];
    return acc;
  }, {});

  const handleOperationSelect = (endpoint) => {
    // 1. Set the selected item for highlighting
    setSelectedNavItem(endpoint);

    // 2. Fetch implementation intelligence if we have the context
    if (
      projectId &&
      (endpoint.operationId || (endpoint.path && endpoint.method))
    ) {
      fetchImplementation(
        projectId,
        endpoint.operationId,
        endpoint.path,
        endpoint.method,
      );
      // 3. Switch the right panel to the implementation view
      setActiveRightPanelTab("implementation");
    }
  };

  return (
    <>
      <div className="panel-header">
        <span className="panel-icon">🌐</span>
        <span className="panel-title">API Structure</span>
      </div>
      <div className="nav-tree">
        {Object.entries(paths).map(([path, methods]) => (
          <div key={path} className="nav-path-group">
            <div className="nav-path-header">
              <code className="nav-path-text">{path}</code>
            </div>
            <div className="nav-methods">
              {methods.map((endpoint) => (
                <button
                  key={endpoint.method}
                  className={`nav-method-item method-${endpoint.method.toLowerCase()} ${
                    selectedNavItem?.path === endpoint.path &&
                    selectedNavItem?.method === endpoint.method
                      ? "active"
                      : ""
                  }`}
                  onClick={() => handleOperationSelect(endpoint)}
                >
                  <span className="method-badge">{endpoint.method}</span>
                  {endpoint.operationId && (
                    <span className="operation-id">{endpoint.operationId}</span>
                  )}
                </button>
              ))}
            </div>
          </div>
        ))}
        {Object.keys(paths).length === 0 && (
          <div className="nav-empty-state">
            <span className="empty-icon">📄</span>
            <p>No endpoints found</p>
            <p className="text-muted text-sm">Add paths to your OpenAPI spec</p>
          </div>
        )}
      </div>
    </>
  );
}

export default NavigationPanel;
