import React from "react";
import Editor from "@monaco-editor/react";
import { useSpecStore } from "../../../store/specStore";

function OperationSpecViewer() {
    const { selectedNavItem, selectedNavItemDetails, isNavItemLoading } = useSpecStore();

    if (isNavItemLoading) {
        return (
            <div className="operation-spec-viewer">
                <div className="panel-header">Operation Specification</div>
                <div className="panel-content">
                    <div className="panel-content-placeholder">Loading operation details...</div>
                </div>
            </div>
        );
    }

    if (!selectedNavItem) {
        return (
            <div className="operation-spec-viewer">
                <div className="panel-header">Operation Specification</div>
                <div className="panel-content">
                    <div className="panel-content-placeholder">Select an operation to view its specification</div>
                </div>
            </div>
        );
    }

    if (!selectedNavItemDetails) {
        return (
            <div className="operation-spec-viewer">
                <div className="panel-header">Operation Specification</div>
                <div className="panel-content">
                    <div className="panel-content-placeholder">Failed to load operation details</div>
                </div>
            </div>
        );
    }

    // Format the tree-shaken JSON for display with Monaco Editor
    const formattedJson = JSON.stringify(selectedNavItemDetails, null, 2);

    return (
        <div className="operation-spec-viewer">
            <div className="panel-header">
                Operation Specification: {selectedNavItem.method.toUpperCase()} {selectedNavItem.path}
            </div>
            <div className="panel-content">
                <div className="monaco-editor-wrapper">
                    <Editor
                        height="100%"
                        theme="vs-dark"
                        language="json"
                        value={formattedJson}
                        options={{
                            readOnly: true,
                            minimap: { enabled: false },
                            scrollBeyondLastLine: false,
                            fontSize: 12,
                            wordWrap: "on",
                            folding: true,
                            foldingHighlight: true,
                            foldingImportsByDefault: false,
                            showFoldingControls: "always",
                        }}
                    />
                </div>
            </div>
        </div>
    );
}

export default OperationSpecViewer;