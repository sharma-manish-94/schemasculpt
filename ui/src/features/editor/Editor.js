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
`;

function SpecEditor() {
  const [specText, setSpecText] = useState(sampleSpec);
  const [errors, setErrors] = useState([]);

  useEffect(() => {
    const timer = setTimeout(() => {
      validateSpec(specText).then(validationErrors => {
        setErrors(validationErrors);
      });
    }, 500);
    return () => clearTimeout(timer);
  }, [specText]);

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
        {errors.length > 0 ? (
          <ul>
            {errors.map((err, index) => (
              <li key={index}>{err.message}</li>
            ))}
          </ul>
        ) : (
          <p className="no-errors">No validation errors found.</p>
        )}
      </div>
    </div>
  );
}

export default SpecEditor;