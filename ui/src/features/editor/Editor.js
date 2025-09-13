import React, { useState, useEffect } from 'react';
import Editor from '@monaco-editor/react';
import { validateSpec } from '../../api/validationService';
import './editor.css';

const sampleSpec = `
openapi: 3.0.0
info:
  title: Simple Pet Store API
  version: 1.0.0
servers:
  - url: http://localhost:8080/api/v1
paths:
  /pets:
    get:
      summary: List all pets
      operationId: listPets
      responses:
        '200':
          description: A paged array of pets
          content:
            application/json:    
              schema:
                type: array
                items:
                  type: string
components:
  schemas:
    UnusedComponent:
      type: object
      properties:
        message:
          type: string
                  `;

function SpecEditor() {
  const [specText, setSpecText] = useState(sampleSpec);
  const [errors, setErrors] = useState([]);
  const [suggestions, setSuggestions] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    const handleValidation = async () => {
      setIsLoading(true);
      const result = await validateSpec(specText);
      if (result.success) {
        setErrors(result.data.errors);
        setSuggestions(result.data.suggestions);
      } else {
        setErrors([{
          message: result.error
        }]);
        setSuggestions([]);
      }
      setIsLoading(false);
    };
    const timer = setTimeout(() => {
      handleValidation();
    }, 500);
    return () => clearTimeout(timer);
  }, [specText]);

  const renderPanelContent = () => {
    if (isLoading) {
      return <p className="loading-text">Validating...</p>
    }

    const hasErrors = errors.length;
    const hasSuggestions = suggestions.length;

    if (!hasErrors && !hasSuggestions) {
      return <p className="no-errors"> No validation errors or suggestions found.</p>
    }

    return (
      <>
        {hasErrors && (
          <div className="result-section">
            <h3 className="result-title-error">Errors</h3>
            <ul>
              {errors.map((err, index) => (
                <li key={`err-${index}`}>{err.message}</li>
              ))}
            </ul>
          </div>
        )}
        {hasSuggestions && (
          <div className="result-section">
            <h3 className="result-title-suggestion">Suggestions</h3>
            <ul>
              {suggestions.map((sug, index) => (
                <li className="suggestion-item" key={`sug-${index}`}>{sug.message}</li>
              ))}
            </ul>
          </div>
        )}
      </>
    );
  };

  return (
    <div className="spec-editor-layout">
      <Editor
        height="75vh"
        theme="vs-dark"
        defaultLanguage="yaml"
        value={specText}
        onChange={setSpecText}
      />
      <div className="error-panel">
        <div className="panel-header">Validation Results</div>
        {renderPanelContent()}
      </div>
    </div>
  );
}

export default SpecEditor;