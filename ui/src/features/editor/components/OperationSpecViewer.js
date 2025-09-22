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
                    version: fullSpec.info?.version || "1.0.0"
                },
                paths: {
                    [selectedNavItem.path]: {
                        [selectedNavItem.method.toLowerCase()]: operationSpec
                    }
                }
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
        return <div className="panel-content-placeholder">No operation selected</div>;
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
                    <span className={`method-badge ${selectedNavItem.method.toLowerCase()}`}>
                        {selectedNavItem.method}
                    </span>
                    <span className="operation-path">{selectedNavItem.path}</span>
                </div>
            </div>

            <div className="operation-json-editor">
                {treeShakenSpec ? (
                    <Editor
                        height="100%"
                        theme="light"
                        language="json"
                        value={treeShakenSpec}
                        options={{
                            readOnly: true,
                            minimap: { enabled: false },
                            scrollBeyondLastLine: false,
                            fontSize: 12,
                            wordWrap: "on",
                            automaticLayout: true
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