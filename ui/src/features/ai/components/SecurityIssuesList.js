/**
 * SecurityIssuesList Component
 * Displays sortable and filterable list of security issues
 */

import React, { useState, useMemo } from "react";

const SecurityIssuesList = ({ issues }) => {
  const [filterSeverity, setFilterSeverity] = useState("all");
  const [filterCategory, setFilterCategory] = useState("all");
  const [sortBy, setSortBy] = useState("severity"); // 'severity', 'category', 'title'
  const [expandedIssue, setExpandedIssue] = useState(null);

  // Get unique categories
  const categories = useMemo(() => {
    const cats = new Set();
    issues.forEach((issue) => {
      if (issue.owasp_category) {
        cats.add(issue.owasp_category);
      }
    });
    return Array.from(cats).sort();
  }, [issues]);

  // Severity order for sorting
  const severityOrder = { critical: 0, high: 1, medium: 2, low: 3, info: 4 };

  // Filter and sort issues
  const filteredAndSortedIssues = useMemo(() => {
    let filtered = issues;

    // Apply severity filter
    if (filterSeverity !== "all") {
      filtered = filtered.filter(
        (issue) => issue.severity?.toLowerCase() === filterSeverity,
      );
    }

    // Apply category filter
    if (filterCategory !== "all") {
      filtered = filtered.filter(
        (issue) => issue.owasp_category === filterCategory,
      );
    }

    // Sort
    const sorted = [...filtered].sort((a, b) => {
      if (sortBy === "severity") {
        const severityA = severityOrder[a.severity?.toLowerCase()] ?? 999;
        const severityB = severityOrder[b.severity?.toLowerCase()] ?? 999;
        return severityA - severityB;
      } else if (sortBy === "category") {
        return (a.owasp_category || "").localeCompare(b.owasp_category || "");
      } else if (sortBy === "title") {
        return (a.title || "").localeCompare(b.title || "");
      }
      return 0;
    });

    return sorted;
  }, [issues, filterSeverity, filterCategory, sortBy]);

  const getSeverityColor = (severity) => {
    const colors = {
      critical: "#dc2626",
      high: "#ea580c",
      medium: "#f59e0b",
      low: "#10b981",
      info: "#3b82f6",
    };
    return colors[severity?.toLowerCase()] || "#6b7280";
  };

  const toggleIssue = (issueId) => {
    setExpandedIssue(expandedIssue === issueId ? null : issueId);
  };

  if (!issues || issues.length === 0) {
    return (
      <div className="security-issues-empty">
        <p>No security issues found! 🎉</p>
      </div>
    );
  }

  return (
    <div className="security-issues-list">
      {/* Filters and Sort */}
      <div className="issues-controls">
        <div className="issues-filters">
          <div className="filter-group">
            <label>Severity:</label>
            <select
              value={filterSeverity}
              onChange={(e) => setFilterSeverity(e.target.value)}
            >
              <option value="all">All ({issues.length})</option>
              <option value="critical">
                Critical (
                {
                  issues.filter((i) => i.severity?.toLowerCase() === "critical")
                    .length
                }
                )
              </option>
              <option value="high">
                High (
                {
                  issues.filter((i) => i.severity?.toLowerCase() === "high")
                    .length
                }
                )
              </option>
              <option value="medium">
                Medium (
                {
                  issues.filter((i) => i.severity?.toLowerCase() === "medium")
                    .length
                }
                )
              </option>
              <option value="low">
                Low (
                {
                  issues.filter((i) => i.severity?.toLowerCase() === "low")
                    .length
                }
                )
              </option>
              <option value="info">
                Info (
                {
                  issues.filter((i) => i.severity?.toLowerCase() === "info")
                    .length
                }
                )
              </option>
            </select>
          </div>

          <div className="filter-group">
            <label>Category:</label>
            <select
              value={filterCategory}
              onChange={(e) => setFilterCategory(e.target.value)}
            >
              <option value="all">All Categories</option>
              {categories.map((cat) => (
                <option key={cat} value={cat}>
                  {cat.replace(/_/g, " ")}
                </option>
              ))}
            </select>
          </div>

          <div className="filter-group">
            <label>Sort by:</label>
            <select value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
              <option value="severity">Severity</option>
              <option value="category">Category</option>
              <option value="title">Title</option>
            </select>
          </div>
        </div>

        <div className="issues-count">
          Showing {filteredAndSortedIssues.length} of {issues.length} issues
        </div>
      </div>

      {/* Issues List */}
      <div className="issues-container">
        {filteredAndSortedIssues.map((issue, idx) => (
          <div
            key={issue.id || idx}
            className={`issue-card ${expandedIssue === issue.id ? "expanded" : ""}`}
          >
            <div className="issue-header" onClick={() => toggleIssue(issue.id)}>
              <div className="issue-title-section">
                <span
                  className="severity-badge"
                  style={{ backgroundColor: getSeverityColor(issue.severity) }}
                >
                  {issue.severity?.toUpperCase()}
                </span>
                <h5 className="issue-title">{issue.title}</h5>
              </div>
              <button className="expand-button">
                {expandedIssue === issue.id ? "▼" : "▶"}
              </button>
            </div>

            <div className="issue-description">{issue.description}</div>

            {expandedIssue === issue.id && (
              <div className="issue-details">
                {/* OWASP Category */}
                {issue.owasp_category && (
                  <div className="issue-detail-section">
                    <h6>OWASP Category</h6>
                    <p className="owasp-tag">
                      {issue.owasp_category.replace(/_/g, " ")}
                    </p>
                  </div>
                )}

                {/* Location */}
                {issue.location && Object.keys(issue.location).length > 0 && (
                  <div className="issue-detail-section">
                    <h6>Location</h6>
                    <pre className="location-code">
                      {JSON.stringify(issue.location, null, 2)}
                    </pre>
                  </div>
                )}

                {/* Recommendation */}
                {issue.recommendation && (
                  <div className="issue-detail-section">
                    <h6>Recommendation</h6>
                    <p className="recommendation-text">
                      {issue.recommendation}
                    </p>
                  </div>
                )}

                {/* Remediation Example */}
                {issue.remediation_example && (
                  <div className="issue-detail-section">
                    <h6>Remediation Example</h6>
                    <pre className="remediation-code">
                      {issue.remediation_example}
                    </pre>
                  </div>
                )}

                {/* CWE ID */}
                {issue.cwe_id && (
                  <div className="issue-detail-section">
                    <h6>CWE</h6>
                    <a
                      href={`https://cwe.mitre.org/data/definitions/${issue.cwe_id.replace("CWE-", "")}.html`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="cwe-link"
                    >
                      {issue.cwe_id}
                    </a>
                  </div>
                )}

                {/* References */}
                {issue.references && issue.references.length > 0 && (
                  <div className="issue-detail-section">
                    <h6>References</h6>
                    <ul className="references-list">
                      {issue.references.map((ref, refIdx) => (
                        <li key={refIdx}>
                          <a
                            href={ref}
                            target="_blank"
                            rel="noopener noreferrer"
                          >
                            {ref}
                          </a>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default SecurityIssuesList;
