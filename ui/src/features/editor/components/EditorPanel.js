import React, { useRef, useEffect } from "react";
import Editor from "@monaco-editor/react";
import { useSpecStore } from "../../../store/specStore";
import { useRequestStore } from "../../../store/requestStore";

function EditorToolbar() {
  const { format, convertToJSON, convertToYAML } = useSpecStore();
  return (
    <div className="editor-toolbar">
      <span className="format-indicator">Format: {format.toUpperCase()}</span>
      <div className="toolbar-buttons">
        <button onClick={convertToJSON} disabled={format === "json"}>
          Convert to JSON
        </button>
        <button onClick={convertToYAML} disabled={format === "yaml"}>
          Convert to YAML
        </button>
      </div>
    </div>
  );
}

function AiAssistantBar() {
  const { aiPrompt, setAiPrompt, submitAiRequest, isLoading } = useSpecStore();

  const handleSubmit = (e) => {
    e.preventDefault();
    submitAiRequest();
  };

  return (
    <form className="ai-assistant-bar" onSubmit={handleSubmit}>
      <input
        type="text"
        className="ai-input"
        placeholder="AI Assistant: e.g., 'add a GET endpoint for /health'"
        value={aiPrompt}
        onChange={(e) => setAiPrompt(e.target.value)}
        disabled={isLoading}
      />
      <button type="submit" className="ai-submit-button" disabled={isLoading}>
        Submit
      </button>
    </form>
  );
}

// Main Editor Panel component
function EditorPanel() {
  const { specText, setSpecText, format } = useSpecStore();
  const editorRef = useRef(null);

  function handleEditorDidMount(editor) {
    editorRef.current = editor;
  }

  // Effect to synchronize programmatic changes to the editor (e.g., from AI or fixes)
  useEffect(() => {
    if (editorRef.current && editorRef.current.getValue() !== specText) {
      editorRef.current.setValue(specText);
    }
  }, [specText]);

  // Effect to parse endpoints whenever specText changes
  const parseEndpoints = useRequestStore((state) => state.parseEndpoints);
  const validateCurrentSpec = useSpecStore(
    (state) => state.validateCurrentSpec
  );

  useEffect(() => {
    // Parse endpoints whenever specText changes (for API Lab)
    parseEndpoints();
    // Debounced validation
    const timer = setTimeout(() => {
      validateCurrentSpec();
    }, 500);
    return () => clearTimeout(timer);
  }, [specText, parseEndpoints, validateCurrentSpec]);

  return (
    <div className="editor-container">
      <EditorToolbar />
      <Editor
        wrapperProps={{ className: "editor-wrapper" }} // Pass class to the wrapper
        height="100%"
        theme="vs-dark"
        language={format}
        value={specText}
        onMount={handleEditorDidMount}
        onChange={(value) => setSpecText(value || "")}
        options={{
          minimap: { enabled: false },
          scrollBeyondLastLine: false,
          fontSize: 12,
          wordWrap: "on",
        }}
      />
      <AiAssistantBar />
    </div>
  );
}

export default EditorPanel;
