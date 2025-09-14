import React, { useEffect, useState, useRef } from 'react';
import Editor from '@monaco-editor/react';
import { Panel, PanelGroup, PanelResizeHandle, } from "react-resizable-panels";
import SwaggerUI from 'swagger-ui-react';
import "swagger-ui-react/swagger-ui.css";
import yaml from 'js-yaml'
import { applyQuickFix, executeAiAction, validateSpec, startMockServer } from '../../api/validationService';
import './editor.css';

// The sampleSpec constant remains the same...
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
    const editorRef = useRef(null);
    const [errors, setErrors] = useState([]);
    const [suggestions, setSuggestions] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [activeTab, setActiveTab] = useState('validation');
    const [format, setFormat] = useState('yaml');
    const [aiPrompt, setAiPrompt] = useState('');
    const [mockServer, setMockServer] = useState({ active: false, url: '', id: '' }); // New state for mock server
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
                                onChange={(value) => setSpecText(value || "")} // Update state on user input
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
                            <button onClick={() => setActiveTab('api_lab')} className={activeTab === 'api_lab' ? 'active' : ''}>API Lab</button> {/* New Tab */}
                        </div>
                        <div className="panel-content">
                            {activeTab === 'validation' && renderValidationContent()}
                            {activeTab === 'visualize' && <SwaggerUI spec={specText} />}
                            {activeTab === 'api_lab' && (
                                <div>
                                    {!mockServer.active ? (
                                        <>
                                            <p>Start an AI-powered mock server based on your current spec.</p>
                                            <button className="ai-submit-button" onClick={handleStartMockServer} disabled={isLoading}>
                                                {isLoading ? 'Starting...' : 'Start AI Mock Server'}
                                            </button>
                                        </>
                                    ) : (
                                        <div>
                                            <h4>Mock Server is Active!</h4>
                                            <p>Base URL:</p>
                                            <pre className="mock-url-display">{mockServer.url}</pre>
                                            <p>You can now make requests to your endpoints, like <code>GET {mockServer.url}/pets</code>, using a tool like Bruno or curl.</p>
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                    </div>
                </Panel>
            </PanelGroup>
        </div>
    );
}

export default SpecEditor;