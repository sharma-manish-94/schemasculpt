import React, { useState, useEffect } from 'react';
import Editor from '@monaco-editor/react';
import {
  Panel,
  PanelGroup,
  PanelResizeHandle,
} from "react-resizable-panels";
import SwaggerUI from 'swagger-ui-react';
import "swagger-ui-react/swagger-ui.css";
import { validateSpec } from '../../api/validationService';
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
  const [errors, setErrors] = useState([]);
  const [suggestions, setSuggestions] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('validation');

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
    const timer = setTimeout(() => { handleValidation(); }, 500);
    return () => clearTimeout(timer);
  }, [specText]);

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
            <ul>{suggestions.map((sug, index) => (<li className="suggestion-item" key={`sug-${index}`}>{sug.message}</li>))}</ul>
          </div>
        )}
      </>
    );
  };

  return (
    <div className="spec-editor-layout">
      <PanelGroup direction="horizontal">
        <Panel defaultSize={60} minSize={30}>
          <div className="editor-wrapper">
            <Editor
              theme="vs-dark"
              defaultLanguage="yaml"
              value={specText}
              onChange={setSpecText}
            />
          </div>
        </Panel>
        <PanelResizeHandle className="resize-handle" />
        <Panel defaultSize={40} minSize={20}>
          <div className="right-panel-container">
            <div className="panel-tabs">
              <button onClick={() => setActiveTab('validation')} className={activeTab === 'validation' ? 'active' : ''}>Validation</button>
              <button onClick={() => setActiveTab('visualize')} className={activeTab === 'visualize' ? 'active' : ''}>Visualize</button>
            </div>
            <div className="panel-content">
              {activeTab === 'validation' && renderValidationContent()}
              {activeTab === 'visualize' && <SwaggerUI spec={specText} />}
            </div>
          </div>
        </Panel>
      </PanelGroup>
    </div>
  );
}

export default SpecEditor;