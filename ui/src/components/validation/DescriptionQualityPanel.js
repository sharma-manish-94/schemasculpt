import React, { useState } from "react";
import "./DescriptionQualityPanel.css";

const DescriptionQualityPanel = ({
  results,
  overallScore,
  patches,
  onApplyPatches,
  isLoading,
}) => {
  const [expandedItems, setExpandedItems] = useState(new Set());

  const toggleExpand = (path) => {
    const newExpanded = new Set(expandedItems);
    if (newExpanded.has(path)) {
      newExpanded.delete(path);
    } else {
      newExpanded.add(path);
    }
    setExpandedItems(newExpanded);
  };

  const getQualityLevelColor = (level) => {
    switch (level) {
      case "EXCELLENT":
        return "#10b981"; // Green
      case "GOOD":
        return "#3b82f6"; // Blue
      case "FAIR":
        return "#f59e0b"; // Orange
      case "POOR":
        return "#ef4444"; // Red
      case "MISSING":
        return "#6b7280"; // Gray
      default:
        return "#6b7280";
    }
  };

  const getQualityLevelIcon = (level) => {
    switch (level) {
      case "EXCELLENT":
        return "✓";
      case "GOOD":
        return "✓";
      case "FAIR":
        return "!";
      case "POOR":
        return "✗";
      case "MISSING":
        return "∅";
      default:
        return "?";
    }
  };

  const getSeverityIcon = (severity) => {
    switch (severity) {
      case "high":
        return "🔴";
      case "medium":
        return "🟡";
      case "low":
        return "🔵";
      default:
        return "ℹ️";
    }
  };

  const formatPath = (path) => {
    // Convert /paths/~1users~1{id}/get/description to /users/{id} GET
    const parts = path.split("/");
    if (parts[1] === "paths") {
      const apiPath = parts[2]?.replace(/~1/g, "/") || "";
      const method = parts[3]?.toUpperCase() || "";
      return `${apiPath} ${method}`;
    } else if (parts[1] === "components" && parts[2] === "schemas") {
      return `Schema: ${parts[3]}`;
    }
    return path;
  };

  const applyAllPatches = () => {
    if (onApplyPatches && patches && patches.length > 0) {
      onApplyPatches(patches);
    }
  };

  const applySinglePatch = (patch) => {
    if (onApplyPatches) {
      onApplyPatches([patch]);
    }
  };

  if (isLoading) {
    return (
      <div className="description-quality-loading">
        <div className="loading-spinner"></div>
        <p>Analyzing description quality...</p>
      </div>
    );
  }

  if (!results || results.length === 0) {
    return (
      <div className="description-quality-empty">
        <p>No descriptions analyzed yet.</p>
        <p className="empty-hint">
          Click "Analyze Descriptions" to check quality.
        </p>
      </div>
    );
  }

  return (
    <div className="description-quality-panel">
      {/* Header with overall score */}
      <div className="quality-header">
        <div className="overall-score">
          <div
            className="score-circle"
            style={{
              borderColor:
                overallScore >= 90
                  ? "#10b981"
                  : overallScore >= 70
                    ? "#3b82f6"
                    : overallScore >= 50
                      ? "#f59e0b"
                      : "#ef4444",
            }}
          >
            <span className="score-value">{overallScore}</span>
            <span className="score-label">Score</span>
          </div>
          <div className="score-info">
            <h3>Description Quality</h3>
            <p>{results.length} items analyzed</p>
          </div>
        </div>
        {patches && patches.length > 0 && (
          <button className="apply-all-btn" onClick={applyAllPatches}>
            ⚡ Apply All Improvements ({patches.length})
          </button>
        )}
      </div>

      {/* Quality legend */}
      <div className="quality-legend">
        <div className="legend-item">
          <span className="legend-dot" style={{ background: "#10b981" }}></span>
          <span>Excellent (90-100)</span>
        </div>
        <div className="legend-item">
          <span className="legend-dot" style={{ background: "#3b82f6" }}></span>
          <span>Good (70-89)</span>
        </div>
        <div className="legend-item">
          <span className="legend-dot" style={{ background: "#f59e0b" }}></span>
          <span>Fair (50-69)</span>
        </div>
        <div className="legend-item">
          <span className="legend-dot" style={{ background: "#ef4444" }}></span>
          <span>Poor (1-49)</span>
        </div>
        <div className="legend-item">
          <span className="legend-dot" style={{ background: "#6b7280" }}></span>
          <span>Missing (0)</span>
        </div>
      </div>

      {/* Results list */}
      <div className="quality-results">
        {results.map((result, index) => {
          const isExpanded = expandedItems.has(result.path);
          const color = getQualityLevelColor(result.level);

          return (
            <div key={index} className="quality-item">
              <div
                className="quality-item-header"
                onClick={() => toggleExpand(result.path)}
                style={{ borderLeftColor: color }}
              >
                <div className="item-info">
                  <span className="quality-icon" style={{ color }}>
                    {getQualityLevelIcon(result.level)}
                  </span>
                  <div className="item-details">
                    <div className="item-path">{formatPath(result.path)}</div>
                    <div className="item-meta">
                      <span className="item-score">
                        Score: {result.qualityScore}
                      </span>
                      <span className="item-level" style={{ color }}>
                        {result.level}
                      </span>
                      {result.issues.length > 0 && (
                        <span className="item-issues">
                          {result.issues.length} issue
                          {result.issues.length > 1 ? "s" : ""}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
                <div className="item-actions">
                  {result.suggestedDescription && (
                    <button
                      className="apply-single-btn"
                      onClick={(e) => {
                        e.stopPropagation();
                        applySinglePatch(result.patch);
                      }}
                      title="Apply this improvement"
                    >
                      ⚡
                    </button>
                  )}
                  <span className="expand-icon">{isExpanded ? "▼" : "▶"}</span>
                </div>
              </div>

              {isExpanded && (
                <div className="quality-item-details">
                  {/* Issues */}
                  {result.issues.length > 0 && (
                    <div className="issues-section">
                      <h4>Issues Found:</h4>
                      <ul className="issues-list">
                        {result.issues.map((issue, i) => (
                          <li key={i} className="issue-item">
                            <span className="issue-severity">
                              {getSeverityIcon(issue.severity)}
                            </span>
                            <span className="issue-type">[{issue.type}]</span>
                            <span className="issue-desc">
                              {issue.description}
                            </span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Suggested improvement */}
                  {result.suggestedDescription && (
                    <div className="suggestion-section">
                      <h4>Suggested Improvement:</h4>
                      <div className="suggested-text">
                        {result.suggestedDescription}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default DescriptionQualityPanel;
