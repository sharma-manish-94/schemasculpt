import React, { useMemo } from 'react';
import RedocViewer from './RedocViewer';
import { useSpecStore } from '../../../store/specStore';

/**
 * DocumentationPanel - Displays full API documentation using Redoc
 *
 * This panel shows the complete OpenAPI specification in a beautiful,
 * readable format with search, deep linking, and download capabilities.
 * Unlike the API Explorer (SwaggerUI), this is focused on documentation
 * rather than interactive testing.
 */
function DocumentationPanel() {
    const specText = useSpecStore((state) => state.specText);

    // Parse the spec from JSON string to object
    const parsedSpec = useMemo(() => {
        if (!specText) return null;

        try {
            return JSON.parse(specText);
        } catch (error) {
            console.error('Failed to parse spec for documentation:', error);
            return null;
        }
    }, [specText]);

    // Show placeholder if no spec is loaded
    if (!parsedSpec) {
        return (
            <div className="documentation-panel">
                <div className="panel-content-placeholder">
                    Load an OpenAPI specification to view documentation
                </div>
            </div>
        );
    }

    return (
        <div className="documentation-panel">
            <RedocViewer
                spec={parsedSpec}
                isLoading={false}
                selectedOperation={null}
            />
        </div>
    );
}

export default DocumentationPanel;
