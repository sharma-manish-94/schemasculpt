/**
 * BlastRadiusPanel Component
 * Displays blast radius analysis results for a selected schema.
 * Shows summary metrics (risk level, percentage) and detailed breakdown
 * (direct dependents, all affected schemas, affected endpoints).
 */

import React, { useState, useCallback } from "react";
import { useSpecStore } from "../../../store/specStore";
import { runBlastRadiusAnalysis } from "../../../api/analysisService";
import "./BlastRadiusPanel.css";

const BlastRadiusPanel = ({ specContent, onHighlightSchemas }) => {
  const { sessionId } = useSpecStore();
  const [schemaName, setSchemaName] = useState("");
  const [analyzing, setAnalyzing] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);

  const getRiskColor = useCallback((riskLevel) => {
    const colors = {
      CRITICAL: "#dc2626",
      HIGH: "#ea580c",
      MEDIUM: "#f59e0b",
      LOW: "#10b981",
    };
    return colors[riskLevel?.toUpperCase()] || "#6b7280";
  }, []);

  const getRiskIcon = useCallback((riskLevel) => {
    const icons = {
      CRITICAL: "🔴",
      HIGH: "🟠",
      MEDIUM: "🟡",
      LOW: "🟢",
    };
    return icons[riskLevel?.toUpperCase()] || "⚪";
  }, []);

  const handleAnalyze = async () => {
    if (!schemaName.trim()) {
      setError("Please enter a schema name");
      return;
    }

    if (!specContent || !sessionId) {
      setError("No specification content or session");
      return;
    }

    setAnalyzing(true);
    setError(null);
    setResults(null);

    try {
      const result = await runBlastRadiusAnalysis(
        sessionId,
        schemaName.trim(),
        specContent,
      );

      if (result.success) {
        setResults(result.data);
        // Trigger highlighting in editor
        if (onHighlightSchemas && result.data.allAffectedSchemas) {
          onHighlightSchemas([
            schemaName.trim(),
            ...result.data.allAffectedSchemas,
          ]);
        }
      } else {
        setError(result.error || "Blast radius analysis failed");
      }
    } catch (err) {
      setError(err.message || "An unexpected error occurred");
    } finally {
      setAnalyzing(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter") {
      handleAnalyze();
    }
  };

  return (
    <div className="blast-radius-panel">
      <div className="blast-radius-header">
        <h3>💥 Blast Radius Analysis</h3>
        <p className="blast-radius-description">
          Analyze the impact of changing a schema on your API
        </p>
      </div>

      <div className="blast-radius-input">
        <input
          type="text"
          placeholder="Enter schema name (e.g., User, Order, Product)"
          value={schemaName}
          onChange={(e) => setSchemaName(e.target.value)}
          onKeyPress={handleKeyPress}
          disabled={analyzing}
          className="schema-input"
        />
        <button
          className="analyze-button"
          onClick={handleAnalyze}
          disabled={analyzing || !schemaName.trim() || !specContent}
        >
          {analyzing ? "⏳ Analyzing..." : "🔍 Analyze"}
        </button>
      </div>

      {error && (
        <div className="blast-radius-error">
          <span className="error-icon">⚠️</span>
          <span>{error}</span>
        </div>
      )}

      {analyzing && (
        <div className="blast-radius-loading">
          <div className="loading-spinner"></div>
          <p>Calculating blast radius for {schemaName}...</p>
        </div>
      )}

      {results && !analyzing && (
        <div className="blast-radius-results">
          {/* Summary Section */}
          <div className="summary-section">
            <div className="summary-header">
              <h4>📊 Impact Summary</h4>
              <span
                className="risk-badge"
                style={{ backgroundColor: getRiskColor(results.riskLevel) }}
              >
                {getRiskIcon(results.riskLevel)} {results.riskLevel} RISK
              </span>
            </div>

            <div className="summary-grid">
              <div className="summary-card">
                <div className="summary-value">{results.percentage}%</div>
                <div className="summary-label">Operations Affected</div>
              </div>
              <div className="summary-card">
                <div className="summary-value">
                  {results.affectedOperations}
                </div>
                <div className="summary-label">
                  of {results.totalOperations} Total
                </div>
              </div>
              <div className="summary-card">
                <div className="summary-value">
                  {results.directDependents?.length || 0}
                </div>
                <div className="summary-label">Direct Dependents</div>
              </div>
              <div className="summary-card">
                <div className="summary-value">
                  {results.allAffectedSchemas?.length || 0}
                </div>
                <div className="summary-label">Total Schemas</div>
              </div>
            </div>
          </div>

          {/* Direct Dependents */}
          {results.directDependents && results.directDependents.length > 0 && (
            <div className="dependents-section">
              <h4>🔗 Direct Dependents</h4>
              <p className="section-description">
                Schemas that directly reference{" "}
                <code>{results.targetSchema}</code>
              </p>
              <div className="schema-chips">
                {results.directDependents.map((schema, idx) => (
                  <span key={idx} className="schema-chip direct">
                    {schema}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* All Affected Schemas */}
          {results.allAffectedSchemas &&
            results.allAffectedSchemas.length > 0 && (
              <div className="affected-schemas-section">
                <h4>📦 All Affected Schemas</h4>
                <p className="section-description">
                  Includes transitive dependencies
                </p>
                <div className="schema-chips">
                  {results.allAffectedSchemas.map((schema, idx) => (
                    <span
                      key={idx}
                      className={`schema-chip ${results.directDependents?.includes(schema) ? "direct" : "transitive"}`}
                    >
                      {schema}
                    </span>
                  ))}
                </div>
              </div>
            )}

          {/* Affected Endpoints */}
          {results.affectedEndpoints &&
            results.affectedEndpoints.length > 0 && (
              <div className="endpoints-section">
                <h4>🌐 Affected Endpoints</h4>
                <p className="section-description">
                  API operations that would be impacted
                </p>
                <div className="endpoints-list">
                  {results.affectedEndpoints.map((endpoint, idx) => {
                    // Parse endpoint format: "operation:METHOD /path"
                    const parts = endpoint.replace("operation:", "").split(" ");
                    const method = parts[0] || "";
                    const path = parts.slice(1).join(" ") || endpoint;

                    return (
                      <div key={idx} className="endpoint-item">
                        <span
                          className={`method-badge ${method.toLowerCase()}`}
                        >
                          {method}
                        </span>
                        <span className="endpoint-path">{path}</span>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

          {/* No Impact */}
          {results.affectedOperations === 0 && (
            <div className="no-impact-section">
              <span className="no-impact-icon">✨</span>
              <h4>No Impact Detected</h4>
              <p>
                This schema is not referenced by any endpoints or other schemas.
                Changes can be made safely.
              </p>
            </div>
          )}
        </div>
      )}

      {!results && !analyzing && !error && (
        <div className="blast-radius-empty">
          <div className="empty-icon">💥</div>
          <h4>Blast Radius Analysis</h4>
          <p>
            Enter a schema name to see how changes would ripple through your
            API.
          </p>
          <ul className="features-list">
            <li>
              <strong>Risk Level:</strong> CRITICAL, HIGH, MEDIUM, or LOW
            </li>
            <li>
              <strong>Direct Dependents:</strong> Schemas that reference this
              one
            </li>
            <li>
              <strong>Transitive Impact:</strong> All indirectly affected
              schemas
            </li>
            <li>
              <strong>Affected Endpoints:</strong> API operations that would
              change
            </li>
          </ul>
        </div>
      )}
    </div>
  );
};

export default BlastRadiusPanel;
