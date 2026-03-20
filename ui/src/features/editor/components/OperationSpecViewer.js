import React, { useMemo } from "react";
import { useSpecStore } from "../../../store/specStore";
import Editor from "@monaco-editor/react";

function OperationSpecViewer() {
  const { selectedNavItem, setSelectedNavItem, specText } = useSpecStore();

  // Tree-shake the OpenAPI spec to show only the selected operation
  const treeShakenSpec = useMemo(() => {
    if (!selectedNavItem || !specText.trim()) {
      return null;
    }

    try {
      const fullSpec = JSON.parse(specText);
      const pathSpec = fullSpec.paths?.[selectedNavItem.path];
      const operationSpec = pathSpec?.[selectedNavItem.method.toLowerCase()];

      if (!operationSpec) {
        return null;
      }

      // Create a minimal spec with just this operation
      const minimalSpec = {
        openapi: fullSpec.openapi || "3.0.0",
        info: {
          title: fullSpec.info?.title || "API",
          version: fullSpec.info?.version || "1.0.0",
        },
        paths: {
          [selectedNavItem.path]: {
            [selectedNavItem.method.toLowerCase()]: operationSpec,
          },
        },
      };

      // Include any components that might be referenced
      if (fullSpec.components) {
        minimalSpec.components = fullSpec.components;
      }

      return JSON.stringify(minimalSpec, null, 2);
    } catch (error) {
      console.error("Error creating tree-shaken spec:", error);
      return JSON.stringify({ error: "Failed to parse OpenAPI spec" }, null, 2);
    }
  }, [selectedNavItem, specText]);

  if (!selectedNavItem) {
    return (
      <div className="panel-content-placeholder">No operation selected</div>
    );
  }

  const handleBackToEditor = () => {
    setSelectedNavItem(null);
  };

  return (
    <div className="operation-spec-viewer">
      <div className="operation-header">
        <button className="back-to-editor-btn" onClick={handleBackToEditor}>
          ← Back to Editor
        </button>
        <div className="operation-title">
          <span
            className={`method-badge ${selectedNavItem.method.toLowerCase()}`}
          >
            {selectedNavItem.method}
          </span>
          <span className="operation-path">{selectedNavItem.path}</span>
        </div>
      </div>

      <div className="operation-json-editor">
        {treeShakenSpec ? (
          <Editor
            height="100%"
            theme="customLight"
            language="json"
            value={treeShakenSpec}
            options={{
              // Basic editor options - keep read-only but allow enhanced features
              readOnly: true,
              minimap: { enabled: true },
              scrollBeyondLastLine: false,
              fontSize: 12,
              lineNumbers: "on",
              lineNumbersMinChars: 3,

              // Code folding and collapsing
              folding: true,
              foldingStrategy: "indentation",
              foldingHighlight: true,
              unfoldOnClickAfterEndOfLine: true,

              // Auto-formatting and prettification
              formatOnPaste: true,
              formatOnType: false, // Keep false for read-only
              autoIndent: "full",

              // Copy-paste and selection
              selectOnLineNumbers: true,
              selectionHighlight: true,
              copyWithSyntaxHighlighting: true,

              // Code suggestions and IntelliSense (disabled for read-only)
              quickSuggestions: false,
              suggestOnTriggerCharacters: false,
              acceptSuggestionOnEnter: "off",

              // Bracket matching and highlighting
              matchBrackets: "always",
              bracketPairColorization: { enabled: true },

              // Scrolling and navigation
              smoothScrolling: true,
              mouseWheelZoom: true,

              // Search and replace
              find: {
                addExtraSpaceOnTop: false,
                autoFindInSelection: "never",
                seedSearchStringFromSelection: "always",
              },

              // Additional features
              contextmenu: true,
              links: true,
              colorDecorators: true,

              // Performance
              automaticLayout: true,
              wordWrap: "on",
            }}
            beforeMount={(monaco) => {
              // Define the same enhanced custom theme for consistency
              monaco.editor.defineTheme("customLight", {
                base: "vs",
                inherit: true,
                rules: [
                  // Force selection highlighting through token rules
                  { token: "", background: "ffffff", foreground: "000000" },
                ],
                colors: {
                  // Primary selection colors - more opaque and visible
                  "editor.selectionBackground": "#0066cc99",
                  "editor.selectionHighlightBackground": "#0066cc66",
                  "editor.inactiveSelectionBackground": "#0066cc77",

                  // Find and match highlighting
                  "editor.findMatchBackground": "#0066cc88",
                  "editor.findMatchHighlightBackground": "#0066cc55",
                  "editor.currentMatchBackground": "#0066ccAA",

                  // Range and word highlighting
                  "editor.rangeHighlightBackground": "#0066cc44",
                  "editor.wordHighlightBackground": "#0066cc33",
                  "editor.wordHighlightStrongBackground": "#0066cc66",

                  // Line highlighting
                  "editor.lineHighlightBackground": "#e6f2ff",
                  "editor.lineHighlightBorder": "#0066cc40",

                  // Additional selection-related colors
                  "editor.selectionForeground": "inherit",
                  "editor.focusedStackFrameHighlightBackground": "#0066cc33",
                  "editor.stackFrameHighlightBackground": "#0066cc22",

                  // Force background colors
                  "editor.background": "#ffffff",
                  "editorWidget.background": "#ffffff",
                  "editorWidget.foreground": "#000000",
                },
              });
              monaco.editor.setTheme("customLight");
            }}
          />
        ) : (
          <div className="operation-error">
            <p>Unable to load operation details</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default OperationSpecViewer;
