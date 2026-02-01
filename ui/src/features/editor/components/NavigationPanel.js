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

    // 2. If it's an operation with an ID, fetch its implementation
    if (endpoint.operationId && projectId) {
      fetchImplementation(projectId, endpoint.operationId);
      // 3. Switch the right panel to the implementation view
      setActiveRightPanelTab("implementation");
    }
  };

  return (
    <>
      <div className="panel-header">
        <span className="panel-icon">🌐</span>
        API Structure
      </div>
      <div className="tree-view">
        <ul>
          {Object.entries(paths).map(([path, methods]) => (
            <li key={path}>
              <span className="tree-item path-item">{path}</span>
              <ul>
                {methods.map((endpoint) => (
                  <li key={endpoint.method}>
                    <span
                      className={`tree-item method-item method-${endpoint.method.toLowerCase()} ${
                        selectedNavItem?.path === endpoint.path &&
                        selectedNavItem?.method === endpoint.method
                          ? "active"
                          : ""
                      }`}
                      onClick={() => handleOperationSelect(endpoint)}
                    >
                      {endpoint.method}
                    </span>
                  </li>
                ))}
              </ul>
            </li>
          ))}
        </ul>
      </div>
    </>
  );
}

export default NavigationPanel;
