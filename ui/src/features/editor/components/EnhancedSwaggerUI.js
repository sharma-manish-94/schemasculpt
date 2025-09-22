import React, { useMemo, useCallback, useRef, useEffect } from "react";
import SwaggerUI from "swagger-ui-react";
import { useSpecStore } from "../../../store/specStore";

function MockServerControls() {
    const {
        isLoading,
        setIsLoading,
        mockServer,
        startMockServer,
        refreshMockServer,
        serverTarget,
        setServerTarget,
        customServerUrl,
        setCustomServerUrl
    } = useSpecStore();

    const handleStartServerClick = async () => {
        setIsLoading(true);
        await startMockServer();
        setIsLoading(false);
    };

    return (
        <div className="mock-server-controls">
            <div className="server-selection">
                <h4>API Server</h4>
                <div className="radio-group">
                    <label className="radio-option">
                        <input
                            type="radio"
                            name="server-target"
                            value="spec"
                            checked={serverTarget === "spec"}
                            onChange={() => setServerTarget("spec")}
                        />
                        <span>Use Spec Servers</span>
                    </label>
                    <label className="radio-option">
                        <input
                            type="radio"
                            name="server-target"
                            value="mock"
                            checked={serverTarget === "mock"}
                            onChange={() => setServerTarget("mock")}
                        />
                        <span>AI Mock Server</span>
                    </label>
                    <label className="radio-option">
                        <input
                            type="radio"
                            name="server-target"
                            value="custom"
                            checked={serverTarget === "custom"}
                            onChange={() => setServerTarget("custom")}
                        />
                        <span>Custom Server</span>
                    </label>
                </div>

                {serverTarget === "custom" && (
                    <div className="custom-server-input">
                        <input
                            type="text"
                            className="text-input"
                            placeholder="Enter your base URL, e.g., http://localhost:9090"
                            value={customServerUrl}
                            onChange={(e) => setCustomServerUrl(e.target.value)}
                        />
                    </div>
                )}

                {serverTarget === "mock" && !mockServer.active && (
                    <div className="mock-server-start">
                        <button
                            className="start-mock-button"
                            onClick={handleStartServerClick}
                            disabled={isLoading}
                        >
                            {isLoading ? "Starting..." : "🚀 Start AI Mock Server"}
                        </button>
                    </div>
                )}

                {serverTarget === "mock" && mockServer.active && (
                    <div className="mock-server-active">
                        <div className="mock-status">
                            <span className="status-indicator active">●</span>
                            <span>Mock Server Active</span>
                        </div>
                        <div className="mock-url-display">
                            <input
                                type="text"
                                className="text-input mock-url"
                                readOnly
                                value={mockServer.url}
                            />
                            <button
                                className="refresh-button"
                                onClick={refreshMockServer}
                                title="Update the mock server with the latest spec from the editor"
                            >
                                🔄
                            </button>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}

function EnhancedSwaggerUI() {
    const {
        specText,
        mockServer,
        serverTarget,
        customServerUrl,
        selectedNavItem
    } = useSpecStore();

    // Ref to store Swagger UI system object for programmatic control
    const swaggerSystemRef = useRef(null);

    // Parse specText for SwaggerUI
    const parsedSpec = useMemo(() => {
        try {
            return JSON.parse(specText);
        } catch (error) {
            console.error('Failed to parse spec for SwaggerUI:', error);
            return null;
        }
    }, [specText]);

    // Extract original server URLs from spec
    const originalServers = useMemo(() => {
        if (!parsedSpec?.servers) return [];
        return parsedSpec.servers.map(server => server.url);
    }, [parsedSpec]);

    // Request interceptor to handle different server targets
    const requestInterceptor = useCallback((req) => {
        console.log('Request interceptor - Original URL:', req.url);
        console.log('Server target:', serverTarget);
        console.log('Mock server:', mockServer);

        // Determine target URL based on server selection
        let targetBaseUrl = null;

        switch (serverTarget) {
            case "mock":
                if (mockServer.active) {
                    targetBaseUrl = mockServer.url;
                    req.headers['X-Mock-Server'] = 'true';
                }
                break;
            case "custom":
                if (customServerUrl) {
                    targetBaseUrl = customServerUrl.replace(/\/$/, ''); // Remove trailing slash
                }
                break;
            case "spec":
            default:
                // Use original spec servers (no modification needed)
                break;
        }

        // Modify URL if we have a target
        if (targetBaseUrl) {
            // Extract the path from the original URL
            try {
                const url = new URL(req.url);
                const path = url.pathname + url.search;
                req.url = targetBaseUrl + path;
                console.log('Request interceptor - Modified URL:', req.url);
            } catch (error) {
                // If URL parsing fails, try simple replacement
                console.warn('URL parsing failed, attempting simple replacement');
                if (originalServers.length > 0) {
                    originalServers.forEach(serverUrl => {
                        if (req.url.includes(serverUrl)) {
                            req.url = req.url.replace(serverUrl, targetBaseUrl);
                        }
                    });
                }
            }
        }

        return req;
    }, [serverTarget, mockServer, customServerUrl, originalServers]);

    // Response interceptor for debugging and potential response modification
    const responseInterceptor = useCallback((response) => {
        console.log('Response interceptor:', {
            url: response.url,
            status: response.status,
            serverTarget
        });

        // Add mock server indicator to response if applicable
        if (serverTarget === "mock" && mockServer.active) {
            console.log('Response from mock server:', response);
        }

        return response;
    }, [serverTarget, mockServer]);

    // Callback when Swagger UI finishes rendering
    const onComplete = useCallback((system) => {
        console.log('Swagger UI loaded, system:', system);
        swaggerSystemRef.current = system;
    }, []);

    // Function to scroll to and highlight a specific operation
    const scrollToOperation = useCallback((path, method) => {
        console.log(`Attempting to scroll to operation: ${method.toUpperCase()} ${path}`);

        // First, try to expand all tags to ensure the operation is visible
        // This is especially important when switching between different tag groups
        setTimeout(() => {
            // Step 1: Expand all tags to make sure operations are visible
            const tagButtons = document.querySelectorAll('.opblock-tag-section .opblock-tag');
            tagButtons.forEach(tagButton => {
                const section = tagButton.closest('.opblock-tag-section');
                if (section && !section.classList.contains('is-open')) {
                    tagButton.click();
                }
            });

            // Step 2: Wait a bit for tag expansion, then find the operation
            setTimeout(() => {
            // Try multiple selectors to find the operation
            const selectors = [
                `[data-path="${path}"][data-method="${method.toLowerCase()}"]`,
                `#operations-${method.toLowerCase()}-${path.replace(/[^a-zA-Z0-9]/g, '_')}`,
                `[id*="${method.toLowerCase()}"]${path.includes('/') ? `[id*="${path.split('/')[1]}"]` : ''}`,
                `.opblock-${method.toLowerCase()}:has([data-path="${path}"])`,
                `.operation-tag-content span:contains("${method.toUpperCase()} ${path}")`,
            ];

            let operationElement = null;
            for (const selector of selectors) {
                try {
                    operationElement = document.querySelector(selector);
                    if (operationElement) {
                        console.log(`Found operation with selector: ${selector}`);
                        break;
                    }
                } catch (e) {
                    // Invalid selector, continue
                }
            }

            // Fallback: search by text content
            if (!operationElement) {
                const allOperations = document.querySelectorAll('.opblock');
                for (const op of allOperations) {
                    const summaryElement = op.querySelector('.opblock-summary');
                    if (summaryElement && summaryElement.textContent.includes(`${method.toUpperCase()} ${path}`)) {
                        operationElement = op;
                        console.log('Found operation by text content');
                        break;
                    }
                }
            }

            if (operationElement) {
                // Expand the operation if it's collapsed
                const button = operationElement.querySelector('.opblock-summary');
                if (button && !operationElement.classList.contains('is-open')) {
                    button.click();
                    console.log('Expanded collapsed operation');
                }

                // Scroll to the operation
                operationElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start',
                    inline: 'nearest'
                });

                // Add a temporary highlight
                operationElement.style.outline = '3px solid var(--primary-blue, #0066cc)';
                operationElement.style.outlineOffset = '2px';
                setTimeout(() => {
                    operationElement.style.outline = '';
                    operationElement.style.outlineOffset = '';
                }, 3000);

                console.log('Successfully scrolled to and highlighted operation');
            } else {
                console.log('Operation element not found, trying alternative approach');

                // Alternative: try to find by operation ID in the actual spec
                if (swaggerSystemRef.current) {
                    try {
                        // Try different ways to access the spec from Swagger UI system
                        let spec = null;
                        const system = swaggerSystemRef.current;

                        // Method 1: Direct spec access
                        if (system.spec && typeof system.spec.resolve === 'function') {
                            spec = system.spec.resolve();
                        }

                        // Method 2: Get state and access spec
                        if (!spec && system.getState) {
                            const state = system.getState();
                            spec = state?.spec?.resolved || state?.spec?.json || state?.spec;
                        }

                        // Method 3: Direct access to parsedSpec we have in component
                        if (!spec) {
                            spec = parsedSpec;
                        }

                        if (spec?.paths?.[path]?.[method.toLowerCase()]) {
                            const operation = spec.paths[path][method.toLowerCase()];
                            if (operation.operationId) {
                                const idSelector = `#operations-${operation.operationId}`;
                                operationElement = document.querySelector(idSelector);
                                if (operationElement) {
                                    operationElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
                                    console.log(`Found operation by operationId: ${operation.operationId}`);
                                    return; // Success, exit early
                                }
                            }
                        }
                    } catch (error) {
                        console.warn('Error accessing spec, will try manual search:', error.message);
                    }
                }

                // Final fallback: Try a more comprehensive DOM search
                console.log('Trying comprehensive DOM search...');
                const allOpBlocks = document.querySelectorAll('.opblock');
                for (const block of allOpBlocks) {
                    const pathEl = block.querySelector('.opblock-summary-path');
                    const methodEl = block.querySelector('.opblock-summary-method');

                    if (pathEl && methodEl) {
                        const blockPath = pathEl.textContent?.trim();
                        const blockMethod = methodEl.textContent?.trim().toLowerCase();

                        if (blockPath === path && blockMethod === method.toLowerCase()) {
                            operationElement = block;
                            console.log('Found operation through comprehensive DOM search');

                            // Expand if collapsed
                            const summary = block.querySelector('.opblock-summary');
                            if (summary && !block.classList.contains('is-open')) {
                                summary.click();
                            }

                            // Scroll and highlight
                            operationElement.scrollIntoView({
                                behavior: 'smooth',
                                block: 'start',
                                inline: 'nearest'
                            });

                            operationElement.style.outline = '3px solid var(--primary-blue, #0066cc)';
                            operationElement.style.outlineOffset = '2px';
                            setTimeout(() => {
                                operationElement.style.outline = '';
                                operationElement.style.outlineOffset = '';
                            }, 3000);

                            break;
                        }
                    }
                }
            }
            }, 200); // Wait for tag expansion
        }, 100); // Initial delay
    }, [parsedSpec]);

    // Effect to handle operation highlighting when selectedNavItem changes
    useEffect(() => {
        if (selectedNavItem) {
            scrollToOperation(selectedNavItem.path, selectedNavItem.method);
        }
    }, [selectedNavItem, scrollToOperation]);

    if (!parsedSpec) {
        return (
            <div className="swagger-ui-container">
                <MockServerControls />
                <div className="panel-content-placeholder">
                    Invalid JSON - cannot display API documentation
                </div>
            </div>
        );
    }

    return (
        <div className="swagger-ui-container">
            <MockServerControls />
            <div className="swagger-ui-wrapper">
                <SwaggerUI
                    spec={parsedSpec}
                    requestInterceptor={requestInterceptor}
                    responseInterceptor={responseInterceptor}
                    onComplete={onComplete}
                    tryItOutEnabled={true}
                    displayRequestDuration={true}
                    filter={true}
                    showExtensions={true}
                    showCommonExtensions={true}
                    docExpansion="none"
                    deepLinking={true}
                    defaultModelsExpandDepth={1}
                    defaultModelExpandDepth={1}
                />
            </div>
        </div>
    );
}

export default EnhancedSwaggerUI;