import React from "react";
import { useSpecStore } from "../../../store/specStore";
import { useRequestStore } from "../../../store/requestStore";

function NavigationPanel() {
  const { endpoints, selectedNavItem, setSelectedNavItem } = useRequestStore();

  const paths = endpoints.reduce((acc, ep) => {
    acc[ep.path] = [...(acc[ep.path] || []), ep];
    return acc;
  }, {});

  return (
    <>
      <div className="panel-header">API Structure</div>
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
                      onClick={() => setSelectedNavItem(endpoint)}
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
