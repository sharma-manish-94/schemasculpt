import { useSpecStore } from "../../../store/specStore";
import React, { useRef, useEffect , useMemo} from "react";
import Editor from "@monaco-editor/react";
import yaml from "js-yaml";
import {updateSessionSpec} from "../../../api/validationService";
import * as websocketService from "../../../api/websocketService";

function EditorToolbar() {
    const { format, convertToJSON, convertToYAML, setSpecText, sessionId } = useSpecStore();
    const fileInputRef = useRef(null);

    const handleLoadClick = () => {
        fileInputRef.current.click();
    }
    const handleFileChange = (event) => {
        const file = event.target.files[0];
        if(!file) {
            return;
        }
        const reader = new FileReader();
        reader.onload = async (e) => {
            let content = e.target.result;
            if (!content.trim().startsWith('{')) {
                try {
                    const jsonObj = yaml.load(content);
                    content = JSON.stringify(jsonObj, null, 2);
                    setSpecText(content);
                    if(sessionId) {
                        await updateSessionSpec(sessionId, content);
                    }
                } catch (err) {
                    console.error("Failed to parse loaded YAML file.", err);
                }
            }
            setSpecText(content);
        };
        reader.readAsText(file);
        event.target.value = null;
    };

    return (
        <div className="editor-toolbar">
            <div>
                <button onClick={handleLoadClick} className="toolbar-button">Load File</button>
                <input
                    type="file"
                    ref={fileInputRef}
                    onChange={handleFileChange}
                    style={{ display: 'none' }}
                    accept=".json, .yaml, .yml"
                />
            </div>
            <div className="toolbar-right-group">
                <span className="format-indicator">Format: {format.toUpperCase()}</span>
                <div className="toolbar-buttons">
                    <button
                        onClick={convertToJSON}
                        disabled={format === 'json'}
                        className={`toolbar-button ${format === 'yaml' ? 'active' : ''}`}
                    >
                        Convert to JSON
                    </button>
                    <button
                        onClick={convertToYAML}
                        disabled={format === 'yaml'}
                        className={`toolbar-button ${format === 'json' ? 'active' : ''}`}
                    >
                        Convert to YAML
                    </button>
                </div>
            </div>
        </div>
    );
}

function AiAssistantBar() {
    const {
        aiPrompt,
        setAiPrompt,
        submitAIRequest,
        isLoading,
        isAiProcessing,
        setActiveTab
    } = useSpecStore();

    const handleSubmit = (e) => {
        e.preventDefault();
        submitAIRequest();
    };

    const handleAdvancedClick = () => {
        setActiveTab('ai_features');
    };

    const isProcessing = isLoading || isAiProcessing;

    return (
        <div className="ai-assistant-container">
            <form className="ai-assistant-bar" onSubmit={handleSubmit}>
                <input
                    type="text"
                    className="ai-input"
                    placeholder="AI Assistant: e.g., 'add a GET endpoint for /health'"
                    value={aiPrompt}
                    onChange={(e) => setAiPrompt(e.target.value)}
                    disabled={isProcessing}
                />
                <button type="submit" className="ai-submit-button" disabled={isProcessing || !aiPrompt.trim()}>
                    {isProcessing ? 'Processing...' : 'Submit'}
                </button>
                <button
                    type="button"
                    className="ai-advanced-button"
                    onClick={handleAdvancedClick}
                    title="Open Advanced AI Features"
                >
                    ⚙️
                </button>
            </form>
        </div>
    );
}

// Main Editor Panel component
function EditorPanel() {
    const { specText, setSpecText, format, validateCurrentSpec, sessionId } = useSpecStore();
    const parseEndpoints = useSpecStore((state) => state.parseEndpoints);

    // This is now the single source of truth for what the editor displays.
    const displayedText = useMemo(() => {
        if (format === 'yaml') {
            try {
                const jsonObject = JSON.parse(specText);
                return yaml.dump(jsonObject);
            } catch (e) {
                return "# Invalid JSON state cannot be converted to YAML";
            }
        }
        return specText;
    }, [specText, format]);

    // Debounced effect to parse and validate whenever the underlying specText changes
    useEffect(() => {
        if (!specText.trim()) {
            return; // Don't process empty specs
        }

        const timer = setTimeout(() => {
            // Parse endpoints for the request panel
            parseEndpoints();
            // Validate the spec
            validateCurrentSpec();

            // Send to backend via WebSocket if we have a session AND valid JSON
            if (sessionId && specText.trim()) {
                // Validate JSON before sending to prevent backend parsing errors
                try {
                    JSON.parse(specText);
                    console.log('Sending valid JSON to backend via WebSocket');
                    websocketService.sendMessage(sessionId, specText);
                } catch (error) {
                    console.log('Skipping WebSocket send - invalid JSON:', error.message);
                    // Don't send invalid JSON to backend, wait for user to fix it
                }
            }
        }, 500);

        return () => clearTimeout(timer);
    }, [specText, sessionId]); // Removed parseEndpoints and validateCurrentSpec from deps to prevent recreation

    return (
        <div className="editor-container">
            <EditorToolbar />
            <div className="editor-wrapper">
                <Editor
                    height="100%"
                    theme="light"
                    language={format}
                    value={displayedText} // <-- The editor's content is now always this value
                    onChange={(value) => {
                        // onChange should only work when in editable 'json' mode
                        if (format === 'json') {
                            setSpecText(value || "");
                        }
                    }}
                    options={{
                        // Basic editor options
                        readOnly: false, // Allow copy-paste in both modes
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
                        formatOnType: true,
                        autoIndent: "full",

                        // Copy-paste and selection
                        selectOnLineNumbers: true,
                        selectionHighlight: true,
                        copyWithSyntaxHighlighting: true,

                        // Code suggestions and IntelliSense
                        quickSuggestions: true,
                        suggestOnTriggerCharacters: true,
                        acceptSuggestionOnEnter: "on",

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
                            seedSearchStringFromSelection: "always"
                        },

                        // Additional features
                        contextmenu: true,
                        links: true,
                        colorDecorators: true,

                        // Performance
                        automaticLayout: true,
                        wordWrap: "on",
                    }}
                />
            </div>
            <AiAssistantBar />
        </div>
    );
}

export default EditorPanel;