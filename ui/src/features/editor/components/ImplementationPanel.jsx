import React from "react";
import { useSpecStore } from "../../../store/specStore";
import { Editor } from "@monaco-editor/react";
import "./ImplementationPanel.css";

const ImplementationPanel = () => {
  const { implementationCode, isFetchingImplementation, implementationError } =
    useSpecStore();

  if (isFetchingImplementation) {
    return (
      <div className="implementation-panel loading-state">
        <div className="loading-spinner"></div>
        <p>Fetching implementation from RepoMind...</p>
      </div>
    );
  }

  if (implementationError) {
    return (
      <div className="implementation-panel error-state">
        <h3>Error</h3>
        <p>{implementationError}</p>
      </div>
    );
  }

  if (!implementationCode) {
    return (
      <div className="implementation-panel empty-state">
        <p>
          Select an endpoint from the navigation panel to view its source code
          implementation.
        </p>
      </div>
    );
  }

  return (
    <div className="implementation-panel">
      <div className="file-path-header">
        <strong>File:</strong> {implementationCode.filePath} (Line:{" "}
        {implementationCode.startLine})
      </div>
      <Editor
        height="calc(100% - 30px)" // Adjust height for the header
        language={implementationCode.language || "plaintext"}
        value={implementationCode.content}
        options={{
          readOnly: true,
          minimap: { enabled: false },
          fontSize: 12,
          wordWrap: "on",
          lineNumbers: "on",
          glyphMargin: false,
        }}
      />
    </div>
  );
};

export default ImplementationPanel;
