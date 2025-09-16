import React from 'react';
import Editor from '@monaco-editor/react'; // For the request body editor
import {useSpecStore} from '../../../store/specStore'; // Connect to our store

function AILabPanel() {
    // Get all necessary state and actions from the store
    const {
        endpoints,
        selectedEndpointIndex,
        setSelectedEndpointIndex,
        serverTarget,
        setServerTarget,
        customServerUrl,
        setCustomServerUrl,
        mockServer,
        startMockServer,
        refreshMockServer,
        pathParams,
        setPathParams,
        requestBody,
        setRequestBody,
        apiResponse,
        isApiRequestLoading,
        sendRequest,
        isLoading // Reusing main isLoading for mock server start
    } = useSpecStore();

    const selectedEndpoint = endpoints[selectedEndpointIndex] || null;
    const pathParameters = selectedEndpoint?.details.parameters?.filter(p => p.in === 'path') || [];
    const hasRequestBody = !!selectedEndpoint?.details.requestBody;

    const handlePathParamChange = (name, value) => {
        setPathParams(prev => ({...prev, [name]: value}));
    };

    return (<div className="api-lab-container">
            <div className="form-group">
                <label>Target Server</label>
                <div className="radio-group">
                    <input type="radio" id="mock-server" name="server-target" value="mock"
                           checked={serverTarget === 'mock'} onChange={() => setServerTarget('mock')}/>
                    <label htmlFor="mock-server">AI Mock Server</label>
                    <input type="radio" id="custom-server" name="server-target" value="custom"
                           checked={serverTarget === 'custom'} onChange={() => setServerTarget('custom')}/>
                    <label htmlFor="custom-server">Custom Server</label>
                </div>
                {serverTarget === 'custom' && (<input type="text" className="text-input"
                                                      placeholder="Enter your base URL, e.g., http://localhost:9090"
                                                      value={customServerUrl}
                                                      onChange={(e) => setCustomServerUrl(e.target.value)}/>)}
                {serverTarget === 'mock' && !mockServer.active && (
                    <button className="start-mock-button" onClick={startMockServer}
                            disabled={isLoading}>{isLoading ? 'Starting...' : 'Start AI Mock Server'}</button>)}
                {serverTarget === 'mock' && mockServer.active && (<div>
                        <div className="mock-url-container">
                            <input type="text" className="text-input" readOnly value={mockServer.url}/>
                            <button className="refresh-button" onClick={refreshMockServer}
                                    title="Update the mock server with the latest spec from the editor">🔄 Refresh
                            </button>
                        </div>
                    </div>)}
            </div>

            <div className="form-group">
                <label htmlFor="endpoint-select">Endpoint</label>
                <select id="endpoint-select" className="select-input" value={selectedEndpointIndex}
                        onChange={e => setSelectedEndpointIndex(e.target.value)}>
                    <option value="" disabled>Select an endpoint to test</option>
                    {endpoints.map((ep, index) => (<option key={`${ep.method}-${ep.path}`} value={index}>
                            {ep.method} {ep.path}
                        </option>))}
                </select>
            </div>

            {/* --- DYNAMIC REQUEST & RESPONSE SECTIONS --- */}
            {selectedEndpoint && (<>
                    <div className="request-builder">
                        <h4>Request</h4>
                        {pathParameters.map(param => (<div className="form-group" key={param.name}>
                                <label htmlFor={`param-${param.name}`}>{param.name} <span
                                    className="param-location">(path)</span></label>
                                <input
                                    type="text"
                                    id={`param-${param.name}`}
                                    className="text-input"
                                    placeholder={param.description || ''}
                                    value={pathParams[param.name] || ''}
                                    onChange={e => handlePathParamChange(param.name, e.target.value)}
                                />
                            </div>))}

                        {hasRequestBody && (<div className="form-group">
                                <label>Body <span className="param-location">(application/json)</span></label>
                                <div className="body-editor-wrapper">
                                    <Editor
                                        height="200px"
                                        language="json"
                                        theme="vs-dark"
                                        value={requestBody}
                                        onChange={(value) => setRequestBody(value || '')}
                                        options={{minimap: {enabled: false}, lineNumbers: 'off'}}
                                    />
                                </div>
                            </div>)}
                        <button className="send-request-button" onClick={sendRequest} disabled={isApiRequestLoading}>
                            {isApiRequestLoading ? 'Sending...' : 'Send Request'}
                        </button>
                    </div>

                    <div className="response-viewer">
                        <h4>Response</h4>
                        {isApiRequestLoading ? (
                            <p className="loading-text">Waiting for response...</p>) : (apiResponse ? (
                                <pre className={apiResponse.success ? 'response-success' : 'response-error'}>
                  {JSON.stringify(apiResponse.data || apiResponse.error, null, 2)}
                </pre>) : <p className="no-errors">Response will be displayed here.</p>)}
                    </div>
                </>)}
        </div>);
}

export default AILabPanel;