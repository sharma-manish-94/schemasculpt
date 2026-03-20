import React from "react";
import { useSpecStore } from "../../../store/specStore";
import { Editor } from "@monaco-editor/react";
import ContractSyncPanel from "./ContractSyncPanel";
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

  if (!implementationCode || !implementationCode.implementation) {
    return (
      <div className="implementation-panel">
        <div className="impl-empty">
          <span className="empty-icon">⚡</span>
          <h3>No Implementation Selected</h3>
          <p>
            Select an endpoint from the navigation panel to view its source code
            implementation and contract verification.
          </p>
        </div>
      </div>
    );
  }

  const { implementation, contractVerification, authVerification } =
    implementationCode;

  return (
    <div className="implementation-panel">
      <div className="impl-main-content">
        <div className="impl-editor-container">
          <div className="impl-header">
            <div className="impl-file-info">
              <span className="file-icon">📄</span>
              <code className="file-path">{implementation.filePath}</code>
              <span className="line-info">Line {implementation.startLine}</span>
            </div>
          </div>
          <div className="impl-editor">
            <Editor
              height="100%"
              language={implementation.language || "plaintext"}
              value={implementation.content}
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
        <ContractSyncPanel
          verification={contractVerification}
          auth={authVerification}
        />
      </div>
    </div>
  );
};

export default ImplementationPanel;
