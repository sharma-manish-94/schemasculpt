import React, { useEffect, useState, useRef } from 'react';
import Editor from '@monaco-editor/react';
import { Panel, PanelGroup, PanelResizeHandle, } from "react-resizable-panels";
import SwaggerUI from 'swagger-ui-react';
import "swagger-ui-react/swagger-ui.css";
import yaml from 'js-yaml'
import { applyQuickFix, executeAiAction, validateSpec, startMockServer, executeProxyRequest, refreshMockSpec } from '../../api/validationService';
import './editor.css';
import axios from 'axios';
import * as websocketService from '../../api/websocketService';


const sampleSpec = `openapi: 3.0.0
info:
  title: Simple Pet Store API
  version: 1.0.0
servers:
  - url: http://localhost:8080/api/v1
paths:
  /pets:
    get:
      summary: List all pets
      responses:
        '200':
          description: A paged array of pets
          content:
            application/json:    
              schema:
                type: array
                items:
                  type: object
                  properties:
                    id:
                      type: integer
                    name:
                      type: string
components:
  schemas:
    UnusedComponent:
      type: object
`;

function SpecEditor() {
    const [specText, setSpecText] = useState(sampleSpec);
    const [sessionId, setSessionId] = useState(null);
    const editorRef = useRef(null);

    // States for linter, AI, etc.
    const [errors, setErrors] = useState([]);
    const [suggestions, setSuggestions] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [activeTab, setActiveTab] = useState('validation');
    const [format, setFormat] = useState('yaml');
    const [aiPrompt, setAiPrompt] = useState('');

    // State for API Lab
    const [endpoints, setEndpoints] = useState([]);
    const [selectedEndpointIndex, setSelectedEndpointIndex] = useState('');
    const [serverTarget, setServerTarget] = useState('mock');
    const [customServerUrl, setCustomServerUrl] = useState('');
    const [mockServer, setMockServer] = useState({ active: false, url: '', id: '' });

    // State for the API Request Builder
    const [pathParams, setPathParams] = useState({});
    const [requestBody, setRequestBody] = useState('');
    const [apiResponse, setApiResponse] = useState(null);
    const [isApiRequestLoading, setIsApiRequestLoading] = useState(false);


    const handlePathParamChange = (name, value) => {
        setPathParams(prev => ({ ...prev, [name]: value }));
    };

    function handleEditorDidMount(editor, monaco) {
        editorRef.current = editor;
    }



    useEffect(() => {
        if (editorRef.current && editorRef.current.getValue() !== specText) {
            editorRef.current.setValue(specText);
        }
    }, [specText]);

    useEffect(() => {
        const trimmedText = specText.trim();
        if (trimmedText.startsWith('{')) {
            setFormat('json');
        } else {
            setFormat('yaml');
        }
    }, [specText]);

    useEffect(() => {
        const handleValidation = async () => {
            setIsLoading(true);
            const result = await validateSpec(specText);
            if (result.success) {
                setErrors(result.data.errors);
                setSuggestions(result.data.suggestions);
            } else {
                setErrors([{ message: result.error }]);
                setSuggestions([]);
            }
            setIsLoading(false);
        };
        const timer = setTimeout(() => {
            handleValidation();
        }, 500);
        return () => clearTimeout(timer);
    }, [specText]);

    useEffect(() => {
        try {
            const specObject = yaml.load(specText);
            const availableEndpoints = [];
            if (specObject && specObject.paths) {
                for (const path in specObject.paths) {
                    for (const method in specObject.paths[path]) {
                        // Check for valid HTTP methods
                        if (['get', 'post', 'put', 'delete', 'patch', 'options', 'head'].includes(method.toLowerCase())) {
                            availableEndpoints.push({
                                path,
                                method: method.toUpperCase(),
                                details: specObject.paths[path][method]
                            });
                        }
                    }
                }
            }
            setEndpoints(availableEndpoints);
            setSelectedEndpointIndex(''); // Reset selection on spec change
            setApiResponse(null); // Clear previous response
        } catch (e) {
            setEndpoints([]); // Clear endpoints if spec is invalid
        }
    }, [specText]);

    useEffect(() => {
        // Function to handle messages received from the server
        const handleMessage = (message) => {
            console.log('Message from server:', message);
            // Here you could update state based on server broadcasts
        };

        // Connect when the component mounts
        websocketService.connect(handleMessage);

        // Disconnect when the component unmounts
        return () => {
            websocketService.disconnect();
        };
    }, []);

    useEffect(() => {
        // This function creates the session when the component first mounts
        const createSession = async () => {
            try {
                const response = await axios.post('http://localhost:8080/api/v1/sessions', sampleSpec, {
                    headers: { 'Content-Type': 'text/plain' }
                });
                const newSessionId = response.data.sessionId;
                setSessionId(newSessionId);
                console.log('Session created with ID:', newSessionId);
            } catch (error) {
                console.error('Failed to create session:', error);
            }
        };
        createSession();
    }, []); // The emp

    const convertToYAML = () => {
        try {
            const jsonObject = JSON.parse(specText);
            const yamlText = yaml.dump(jsonObject);
            setSpecText(yamlText);
        } catch (error) {
            alert("Could not convert to YAML. Please ensure the content is valid JSON.")
        }
    };

    const convertToJSON = () => {
        try {
            const jsonObject = yaml.load(specText);
            const jsonText = JSON.stringify(jsonObject, null, 2);
            setSpecText(jsonText);
        } catch (error) {
            alert("Could not convert to JSON. Please ensure the content is valid YAML.");
        }
    }

    const handleQuickFix = async (suggestion) => {
        const result = await applyQuickFix({
            specText: specText,
            ruleId: suggestion.ruleId,
            context: suggestion.context,
            format: format
        });
        if (result && result.updatedSpecText) {
            setSpecText(result.updatedSpecText);
        }
    }

    const handleAiSubmit = async (e) => {
        e.preventDefault();
        if (!aiPrompt.trim()) return;

        setIsLoading(true);
        const result = await executeAiAction(specText, aiPrompt);
        if (result && result.updatedSpecText) {
            // This will now trigger the synchronization effect above
            setSpecText(result.updatedSpecText);
        }
        setAiPrompt('');
        setIsLoading(false);
    };

    const handleStartMockServer = async () => {
        setIsLoading(true);
        const result = await startMockServer(specText);
        if (result.success) {
            setMockServer({ active: true, url: `http://localhost:8000${result.data.base_url}`, id: result.data.mock_id });
            setActiveTab('api_lab');
        } else {
            alert(`Error: ${result.error}`);
        }
        setIsLoading(false);
    };

    const handleRefreshMock = async () => {
        if (!mockServer.active) return;

        const result = await refreshMockSpec(mockServer.id, specText);
        if (result.success) {
            alert("Mock server spec has been updated!");
        } else {
            alert(`Error: ${result.error}`);
        }
    };

    const handleSendRequest = async () => {
        const endpoint = endpoints[selectedEndpointIndex];
        if (!endpoint) return;

        let baseUrl = serverTarget === 'mock' ? mockServer.url : customServerUrl;
        if (serverTarget === 'mock' && !mockServer.active) {
            alert("Please start the AI Mock Server first.");
            return;
        }
        if (!baseUrl) {
            alert("Please set a target server URL.");
            return;
        }

        // Replace path parameters in the URL
        let finalUrl = baseUrl + endpoint.path;
        for (const paramName in pathParams) {
            finalUrl = finalUrl.replace(`{${paramName}}`, pathParams[paramName]);
        }

        setIsApiRequestLoading(true);
        setApiResponse(null);
        const result = await executeProxyRequest({
            method: endpoint.method,
            url: finalUrl,
            headers: { 'Content-Type': 'application/json' },
            body: requestBody || null,
        });

        setApiResponse(result);
        setIsApiRequestLoading(false);
    };

    const handleEditorChange = (value) => {
        const newContent = value || "";
        setSpecText(newContent);

        // Only send a message if we have a valid session ID
        if (sessionId) {
            websocketService.sendMessage(sessionId, newContent);
        }
    };


    const renderValidationContent = () => {
        if (isLoading) {
            return <p className="loading-text">Validating...</p>;
        }
        const hasErrors = errors.length > 0;
        const hasSuggestions = suggestions.length > 0;
        if (!hasErrors && !hasSuggestions) {
            return <p className="no-errors">No validation errors or suggestions found.</p>;
        }
        return (
            <>
                {hasErrors && (
                    <div className="result-section">
                        <h3 className="result-title-error">Errors</h3>
                        <ul>{errors.map((err, index) => (<li key={`err-${index}`}>{err.message}</li>))}</ul>
                    </div>
                )}
                {hasSuggestions && (
                    <div className="result-section">
                        <h3 className="result-title-suggestion">Suggestions</h3>
                        <ul>
                            {suggestions.map((sug, index) => (
                                <li className="suggestion-item" key={`sug-${index}`}>
                                    {sug.message}
                                    {sug.ruleId && (
                                        <button className="fix-button" onClick={() => handleQuickFix(sug)}>Fix</button>
                                    )}
                                </li>
                            ))}
                        </ul>
                    </div>
                )}
            </>
        );
    };

    const renderApiLabContent = () => {
        const selectedEndpoint = endpoints[selectedEndpointIndex] || null;
        const pathParameters = selectedEndpoint?.details.parameters?.filter(p => p.in === 'path') || [];
        const hasRequestBody = !!selectedEndpoint?.details.requestBody;

        return (
            <div className="api-lab-container">
                <div className="form-group">
                    <label>Target Server</label>
                    <div className="radio-group">
                        <input type="radio" id="mock-server" name="server-target" value="mock" checked={serverTarget === 'mock'} onChange={() => setServerTarget('mock')} />
                        <label htmlFor="mock-server">AI Mock Server</label>
                        <input type="radio" id="custom-server" name="server-target" value="custom" checked={serverTarget === 'custom'} onChange={() => setServerTarget('custom')} />
                        <label htmlFor="custom-server">Custom Server</label>
                    </div>
                    {serverTarget === 'custom' && (
                        <input type="text" className="text-input" placeholder="Enter your base URL, e.g., http://localhost:9090" value={customServerUrl} onChange={(e) => setCustomServerUrl(e.target.value)} />
                    )}
                    {serverTarget === 'mock' && !mockServer.active && (
                        <button className="start-mock-button" onClick={handleStartMockServer} disabled={isLoading}>{isLoading ? 'Starting...' : 'Start AI Mock Server'}</button>
                    )}
                    {serverTarget === 'mock' && mockServer.active && (
                        <div>
                            <div className="mock-url-container">
                                <input type="text" className="text-input" readOnly value={mockServer.url} />
                                <button className="refresh-button" onClick={handleRefreshMock} title="Update the mock server with the latest spec from the editor">🔄 Refresh</button>
                            </div>
                        </div>
                    )}
                </div>

                <div className="form-group">
                    <label htmlFor="endpoint-select">Endpoint</label>
                    <select id="endpoint-select" className="select-input" value={selectedEndpointIndex} onChange={e => { setSelectedEndpointIndex(e.target.value); setPathParams({}); setRequestBody(''); setApiResponse(null); }}>
                        <option value="" disabled>Select an endpoint to test</option>
                        {endpoints.map((ep, index) => (
                            <option key={`${ep.method}-${ep.path}`} value={index}>
                                {ep.method} {ep.path}
                            </option>
                        ))}
                    </select>
                </div>

                {/* --- DYNAMIC REQUEST & RESPONSE SECTIONS --- */}
                {selectedEndpoint && (
                    <>
                        <div className="request-builder">
                            <h4>Request</h4>
                            {pathParameters.map(param => (
                                <div className="form-group" key={param.name}>
                                    <label htmlFor={`param-${param.name}`}>{param.name} <span className="param-location">(path)</span></label>
                                    <input
                                        type="text"
                                        id={`param-${param.name}`}
                                        className="text-input"
                                        placeholder={param.description || ''}
                                        value={pathParams[param.name] || ''}
                                        onChange={e => handlePathParamChange(param.name, e.target.value)}
                                    />
                                </div>
                            ))}

                            {hasRequestBody && (
                                <div className="form-group">
                                    <label>Body <span className="param-location">(application/json)</span></label>
                                    <div className="body-editor-wrapper">
                                        <Editor
                                            height="200px"
                                            language="json"
                                            theme="vs-dark"
                                            value={requestBody}
                                            onChange={(value) => setRequestBody(value || '')}
                                            options={{ minimap: { enabled: false }, lineNumbers: 'off' }}
                                        />
                                    </div>
                                </div>
                            )}
                            <button className="send-request-button" onClick={handleSendRequest} disabled={isApiRequestLoading}>
                                {isApiRequestLoading ? 'Sending...' : 'Send Request'}
                            </button>
                        </div>

                        <div className="response-viewer">
                            <h4>Response</h4>
                            {isApiRequestLoading ? (
                                <p className="loading-text">Waiting for response...</p>
                            ) : (
                                apiResponse ? (
                                    <pre className={apiResponse.success ? 'response-success' : 'response-error'}>
                                        {JSON.stringify(apiResponse.data || apiResponse.error, null, 2)}
                                    </pre>
                                ) : <p className="no-errors">Response will be displayed here.</p>
                            )}
                        </div>
                    </>
                )}
            </div>
        );
    };

    return (
        <div className="spec-editor-layout">
            <PanelGroup direction="horizontal">
                <Panel defaultSize={60} minSize={30}>
                    <div className="editor-container">
                        <div className="editor-toolbar">
                            <span className="format-indicator">Format: {format.toUpperCase()}</span>
                            <div className="toolbar-buttons">
                                <button onClick={convertToJSON} disabled={format === 'json'}>Convert to JSON</button>
                                <button onClick={convertToYAML} disabled={format === 'yaml'}>Convert to YAML</button>
                            </div>
                        </div>
                        <div className="editor-wrapper">
                            <Editor
                                theme="vs-dark"
                                language={format}
                                defaultValue={specText} // Use defaultValue for the initial load
                                onMount={handleEditorDidMount} // Get the editor instance when it mounts
                                onChange={handleEditorChange}
                            />
                        </div>
                        <form className="ai-assistant-bar" onSubmit={handleAiSubmit}>
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
                    </div>
                </Panel>
                <PanelResizeHandle className="resize-handle" />
                <Panel defaultSize={40} minSize={20}>
                    <div className="right-panel-container">
                        <div className="panel-tabs">
                            <button onClick={() => setActiveTab('validation')} className={activeTab === 'validation' ? 'active' : ''}>Validation</button>
                            <button onClick={() => setActiveTab('visualize')} className={activeTab === 'visualize' ? 'active' : ''}>Visualize</button>
                            <button onClick={() => setActiveTab('api_lab')} className={activeTab === 'api_lab' ? 'active' : ''}>API Lab</button>
                        </div>
                        <div className="panel-content">
                            {activeTab === 'validation' && renderValidationContent()}
                            {activeTab === 'visualize' && <SwaggerUI spec={specText} />}
                            {activeTab === 'api_lab' && renderApiLabContent()}
                        </div>
                    </div>
                </Panel>
            </PanelGroup>
        </div>
    );
}

export default SpecEditor;