import React from "react";
import { useSpecStore } from "../../../store/specStore";
import { Editor } from "@monaco-editor/react";
import "./ImplementationPanel.css";

const ImplementationPanel = () => {
  const { implementationCode, isFetchingImplementation, implementationError } =
    useSpecStore();

  if (isFetchingImplementation) {
    return (
      <div className="implementation-panel">
        <div className="impl-loading">
          <div className="loading-spinner"></div>
          <p>Fetching implementation from RepoMind...</p>
        </div>
      </div>
    );
  }

  if (implementationError) {
    return (
      <div className="implementation-panel">
        <div className="impl-error">
          <span className="error-icon">⚠️</span>
          <h3>Error fetching implementation</h3>
          <p>{implementationError}</p>
        </div>
      </div>
    );
  }

  if (!implementationCode) {
    return (
      <div className="implementation-panel">
        <div className="impl-empty">
          <span className="empty-icon">⚡</span>
          <h3>No Implementation Selected</h3>
          <p>
            Select an endpoint from the navigation panel to view its source code
            implementation.
          </p>
          <div className="impl-features">
            <div className="feature-item">
              <span>📁</span>
              <span>View linked source files</span>
            </div>
            <div className="feature-item">
              <span>📊</span>
              <span>Code complexity metrics</span>
            </div>
            <div className="feature-item">
              <span>🧪</span>
              <span>Related test coverage</span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Extract metrics from implementationCode if available
  const metrics = implementationCode.metrics || {};

  return (
    <div className="implementation-panel">
      <div className="impl-header">
        <div className="impl-file-info">
          <span className="file-icon">📄</span>
          <code className="file-path">{implementationCode.filePath}</code>
          <span className="line-info">Line {implementationCode.startLine}</span>
        </div>
        {Object.keys(metrics).length > 0 && (
          <div className="impl-metrics">
            {metrics.complexity && (
              <span className="metric" title="Cyclomatic Complexity">
                📊 {metrics.complexity}
              </span>
            )}
            {metrics.testCount && (
              <span className="metric" title="Test Count">
                🧪 {metrics.testCount}
              </span>
            )}
            {metrics.owner && (
              <span className="metric" title="Code Owner">
                👤 {metrics.owner}
              </span>
            )}
          </div>
        )}
      </div>
      <div className="impl-editor">
        <Editor
          height="100%"
          language={implementationCode.language || "plaintext"}
          value={implementationCode.content}
          theme="vs-light"
          options={{
            readOnly: true,
            minimap: { enabled: false },
            fontSize: 13,
            fontFamily: "var(--font-mono)",
            wordWrap: "on",
            lineNumbers: "on",
            glyphMargin: false,
            folding: true,
            scrollBeyondLastLine: false,
            renderLineHighlight: "line",
            padding: { top: 12, bottom: 12 },
          }}
        />
      </div>
    </div>
  );
};

export default ImplementationPanel;
