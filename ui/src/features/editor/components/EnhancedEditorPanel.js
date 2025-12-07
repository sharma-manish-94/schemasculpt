import { useSpecStore } from "../../../store/specStore";
import { useAuth } from "../../../contexts/AuthContext";
import { projectAPI } from "../../../api/projectAPI";
import React, { useRef, useEffect, useMemo, useState } from "react";
import Editor from "@monaco-editor/react";
import yaml from "js-yaml";
import { updateSessionSpec } from "../../../api/validationService";
import * as websocketService from "../../../api/websocketService";

function EditorToolbar({ project }) {
    const { format, convertToJSON, convertToYAML, setSpecText, sessionId, specText } = useSpecStore();
    const fileInputRef = useRef(null);
    const [saving, setSaving] = useState(false);
    const [loadingVersions, setLoadingVersions] = useState(false);
    const [versions, setVersions] = useState([]);
    const [showVersions, setShowVersions] = useState(false);
    const [showCommitModal, setShowCommitModal] = useState(false);
    const [commitMessage, setCommitMessage] = useState('');

    const handleLoadClick = () => {
        fileInputRef.current.click();
    };

    const handleFileChange = (event) => {
        const file = event.target.files[0];
        if (!file) {
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
                    if (sessionId) {
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

    const handlePrettify = () => {
        if (format === 'json') {
            try {
                const formatted = JSON.stringify(JSON.parse(specText), null, 2);
                setSpecText(formatted);
            } catch (e) {
                console.error('Invalid JSON, cannot format:', e);
                alert('Cannot prettify: Invalid JSON format');
            }
        }
    };

    const handleDownload = () => {
        const content = format === 'yaml' ?
            yaml.dump(JSON.parse(specText)) :
            specText;
        const filename = `openapi-spec.${format === 'yaml' ? 'yaml' : 'json'}`;
        const blob = new Blob([content], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    };

    const handleSaveVersionClick = () => {
        if (!project) {
            alert('No project selected');
            return;
        }
        setCommitMessage('');
        setShowCommitModal(true);
    };

    const handleSaveVersion = async () => {
        if (!commitMessage.trim()) {
            return;
        }

        setSaving(true);
        setShowCommitModal(false);
        try {
            const specData = {
                specContent: specText,
                specFormat: format,
                commitMessage: commitMessage.trim()
            };

            await projectAPI.saveSpecification(project.id, specData);
            alert('Version saved successfully!');
            setCommitMessage('');
            // Refresh versions list if it's open
            if (showVersions) {
                await loadVersions();
            }
        } catch (error) {
            console.error('Failed to save version:', error);
            alert(error.response?.data?.message || 'Failed to save version');
        } finally {
            setSaving(false);
        }
    };

    const loadVersions = async () => {
        if (!project) return;

        setLoadingVersions(true);
        try {
            const versionList = await projectAPI.getSpecificationVersions(project.id);
            setVersions(versionList);
        } catch (error) {
            console.error('Failed to load versions:', error);
            alert('Failed to load versions');
        } finally {
            setLoadingVersions(false);
        }
    };

    const handleLoadVersion = async (version) => {
        if (!project) return;

        try {
            const spec = await projectAPI.getSpecificationVersion(project.id, version);
            setSpecText(spec.specContent);
            setShowVersions(false);
            if (sessionId) {
                await updateSessionSpec(sessionId, spec.specContent);
            }
        } catch (error) {
            console.error('Failed to load version:', error);
            alert('Failed to load version');
        }
    };

    const toggleVersions = async () => {
        if (!showVersions && versions.length === 0) {
            await loadVersions();
        }
        setShowVersions(!showVersions);
    };

    // Close dropdown when clicking outside
    useEffect(() => {
        const handleClickOutside = (event) => {
            if (showVersions && !event.target.closest('.version-dropdown') && !event.target.closest('[title="Load previous version"]')) {
                setShowVersions(false);
            }
        };

        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, [showVersions]);

    return (
        <div className="editor-toolbar">
            <div className="toolbar-left-group">
                <button onClick={handleLoadClick} className="toolbar-button">
                    📁 Load File
                </button>
                <button onClick={handleDownload} className="toolbar-button">
                    💾 Download
                </button>
                {project && (
                    <>
                        <button
                            onClick={handleSaveVersionClick}
                            disabled={saving}
                            className="toolbar-button save-version-button"
                            title="Save current spec as new version"
                        >
                            {saving ? '⏳ Saving...' : '🔖 Save Version'}
                        </button>
                        <div style={{ position: 'relative' }}>
                            <button
                                onClick={toggleVersions}
                                className="toolbar-button"
                                title="Load previous version"
                            >
                                📜 Versions
                            </button>
                            {showVersions && (
                                <div className="version-dropdown">
                                    {loadingVersions ? (
                                        <div className="version-item">Loading versions...</div>
                                    ) : versions.length === 0 ? (
                                        <div className="version-item">No versions yet</div>
                                    ) : (
                                        versions.map((v) => (
                                            <div
                                                key={v.version}
                                                className="version-item"
                                                onClick={() => handleLoadVersion(v.version)}
                                            >
                                                <div className="version-header">
                                                    <span className="version-number">{v.version}</span>
                                                    {v.isCurrent && <span className="current-badge">Current</span>}
                                                </div>
                                                <div className="version-date">
                                                    {new Date(v.createdAt).toLocaleString()}
                                                </div>
                                            </div>
                                        ))
                                    )}
                                </div>
                            )}
                        </div>
                    </>
                )}

                {/* Commit Message Modal */}
                {showCommitModal && (
                    <div className="commit-modal-overlay" onClick={() => setShowCommitModal(false)}>
                        <div className="commit-modal" onClick={(e) => e.stopPropagation()}>
                            <div className="commit-modal-header">
                                <h3>💾 Save New Version</h3>
                                <button
                                    className="commit-modal-close"
                                    onClick={() => setShowCommitModal(false)}
                                >
                                    ✕
                                </button>
                            </div>
                            <div className="commit-modal-body">
                                <label htmlFor="commit-message">Commit Message</label>
                                <textarea
                                    id="commit-message"
                                    className="commit-message-input"
                                    placeholder="Describe what changed in this version..."
                                    value={commitMessage}
                                    onChange={(e) => setCommitMessage(e.target.value)}
                                    rows={3}
                                    autoFocus
                                    onKeyDown={(e) => {
                                        if (e.key === 'Enter' && e.ctrlKey) {
                                            handleSaveVersion();
                                        }
                                    }}
                                />
                                <div className="commit-modal-hint">
                                    💡 Tip: Press <kbd>Ctrl + Enter</kbd> to save quickly
                                </div>
                            </div>
                            <div className="commit-modal-footer">
                                <button
                                    className="btn-cancel-commit"
                                    onClick={() => setShowCommitModal(false)}
                                >
                                    Cancel
                                </button>
                                <button
                                    className="btn-save-commit"
                                    onClick={handleSaveVersion}
                                    disabled={!commitMessage.trim()}
                                >
                                    💾 Save Version
                                </button>
                            </div>
                        </div>
                    </div>
                )}
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
                        JSON
                    </button>
                    <button
                        onClick={convertToYAML}
                        disabled={format === 'yaml'}
                        className={`toolbar-button ${format === 'json' ? 'active' : ''}`}
                    >
                        YAML
                    </button>
                    <button
                        onClick={handlePrettify}
                        disabled={format === 'yaml'}
                        className="toolbar-button prettify-button"
                        title="Format/Prettify JSON"
                    >
                        ✨ Prettify
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

// Enhanced Editor Panel component
function EnhancedEditorPanel({ project }) {
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
    }, [specText, sessionId, parseEndpoints, validateCurrentSpec]);

    return (
        <div className="editor-container">
            <EditorToolbar project={project} />
            <div className="editor-wrapper">
                <Editor
                    height="100%"
                    theme="customLight"
                    language={format}
                    value={displayedText}
                    onChange={(value) => {
                        // onChange should only work when in editable 'json' mode - exactly like original
                        if (format === 'json') {
                            setSpecText(value || "");
                        }
                    }}
                    options={{
                        // Basic editor options - exactly like original
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
                    beforeMount={(monaco) => {
                        // Define a custom theme to ensure proper selection highlighting
                        monaco.editor.defineTheme('customLight', {
                            base: 'vs',
                            inherit: true,
                            rules: [
                                // Force selection highlighting through token rules
                                { token: '', background: 'ffffff', foreground: '000000' }
                            ],
                            colors: {
                                // Primary selection colors - more opaque and visible
                                'editor.selectionBackground': '#0066cc99',
                                'editor.selectionHighlightBackground': '#0066cc66',
                                'editor.inactiveSelectionBackground': '#0066cc77',

                                // Find and match highlighting
                                'editor.findMatchBackground': '#0066cc88',
                                'editor.findMatchHighlightBackground': '#0066cc55',
                                'editor.currentMatchBackground': '#0066ccAA',

                                // Range and word highlighting
                                'editor.rangeHighlightBackground': '#0066cc44',
                                'editor.wordHighlightBackground': '#0066cc33',
                                'editor.wordHighlightStrongBackground': '#0066cc66',

                                // Line highlighting
                                'editor.lineHighlightBackground': '#e6f2ff',
                                'editor.lineHighlightBorder': '#0066cc40',

                                // Additional selection-related colors
                                'editor.selectionForeground': 'inherit',
                                'editor.focusedStackFrameHighlightBackground': '#0066cc33',
                                'editor.stackFrameHighlightBackground': '#0066cc22',

                                // Force background colors
                                'editor.background': '#ffffff',
                                'editorWidget.background': '#ffffff',
                                'editorWidget.foreground': '#000000'
                            }
                        });

                        // Set the custom theme
                        monaco.editor.setTheme('customLight');
                    }}
                />
            </div>
            <AiAssistantBar />
        </div>
    );
}

export default EnhancedEditorPanel;