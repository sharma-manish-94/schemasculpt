import React from "react";
import { DiffEditor } from "@monaco-editor/react";
import "./CodeDiffViewer.css";

const CodeDiffViewer = ({ originalCode, modifiedCode, language }) => {
  return (
    <div className="code-diff-viewer">
      <div className="diff-header">
        <div className="header-original">Original Code</div>
        <div className="header-modified">Suggested Fix</div>
      </div>
      <DiffEditor
        height="300px"
        language={language}
        original={originalCode}
        modified={modifiedCode}
        theme="vs-dark"
        options={{
          readOnly: true,
          renderSideBySide: true,
          minimap: { enabled: false },
          fontSize: 12,
        }}
      />
    </div>
  );
};

export default CodeDiffViewer;
