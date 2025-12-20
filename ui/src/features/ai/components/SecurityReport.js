/**
 * SecurityReport Component
 * Displays detailed security analysis results from all analyzers
 */

import React from "react";

const SecurityReport = ({ report }) => {
  if (!report) return null;

  const getScoreColor = (score) => {
    if (score >= 80) return "#10b981";
    if (score >= 60) return "#f59e0b";
    if (score >= 40) return "#ea580c";
    return "#dc2626";
  };

  const ScoreBar = ({ score, label }) => (
    <div className="score-bar-container">
      <div className="score-bar-header">
        <span className="score-bar-label">{label}</span>
        <span
          className="score-bar-value"
          style={{ color: getScoreColor(score) }}
        >
          {score.toFixed(1)}
        </span>
      </div>
      <div className="score-bar-track">
        <div
          className="score-bar-fill"
          style={{
            width: `${score}%`,
            backgroundColor: getScoreColor(score),
          }}
        />
      </div>
    </div>
  );

  const issueCountBySeverity = (issues, severity) => {
    return (
      issues?.filter(
        (issue) => issue.severity?.toLowerCase() === severity.toLowerCase(),
      ).length || 0
    );
  };

  return (
    <div className="security-report">
      {/* Score Breakdown */}
      <div className="security-section">
        <h4>Security Scores</h4>
        <div className="score-breakdown">
          <ScoreBar
            score={report.authentication?.score || 0}
            label="Authentication"
          />
          <ScoreBar
            score={report.authorization?.score || 0}
            label="Authorization"
          />
          <ScoreBar
            score={report.data_exposure?.score || 0}
            label="Data Protection"
          />
          <ScoreBar
            score={report.owasp_compliance?.compliance_percentage || 0}
            label="OWASP Compliance"
          />
        </div>
      </div>

      {/* Authentication Analysis */}
      <div className="security-section">
        <h4>🔐 Authentication Analysis</h4>
        <div className="analysis-grid">
          <div className="analysis-stat">
            <span className="stat-label">Has Authentication</span>
            <span
              className={`stat-value ${report.authentication?.has_authentication ? "positive" : "negative"}`}
            >
              {report.authentication?.has_authentication ? "✓ Yes" : "✗ No"}
            </span>
          </div>
          <div className="analysis-stat">
            <span className="stat-label">Schemes</span>
            <span className="stat-value">
              {report.authentication?.authentication_schemes?.join(", ") ||
                "None"}
            </span>
          </div>
          <div className="analysis-stat">
            <span className="stat-label">Unprotected Endpoints</span>
            <span
              className={`stat-value ${report.authentication?.unprotected_endpoints > 0 ? "warning" : "positive"}`}
            >
              {report.authentication?.unprotected_endpoints || 0}
            </span>
          </div>
          <div className="analysis-stat">
            <span className="stat-label">Issues Found</span>
            <span className="stat-value">
              {report.authentication?.issues?.length || 0}
            </span>
          </div>
        </div>
      </div>

      {/* Authorization Analysis */}
      <div className="security-section">
        <h4>🛡️ Authorization Analysis</h4>
        <div className="analysis-grid">
          <div className="analysis-stat">
            <span className="stat-label">RBAC Implemented</span>
            <span
              className={`stat-value ${report.authorization?.rbac_implemented ? "positive" : "negative"}`}
            >
              {report.authorization?.rbac_implemented ? "✓ Yes" : "✗ No"}
            </span>
          </div>
          <div className="analysis-stat">
            <span className="stat-label">Protected Endpoints</span>
            <span className="stat-value positive">
              {report.authorization?.protected_endpoints || 0}
            </span>
          </div>
          <div className="analysis-stat">
            <span className="stat-label">Unprotected Endpoints</span>
            <span
              className={`stat-value ${report.authorization?.unprotected_endpoints > 0 ? "warning" : "positive"}`}
            >
              {report.authorization?.unprotected_endpoints || 0}
            </span>
          </div>
          <div className="analysis-stat">
            <span className="stat-label">Issues Found</span>
            <span className="stat-value">
              {report.authorization?.issues?.length || 0}
            </span>
          </div>
        </div>
      </div>

      {/* Data Exposure Analysis */}
      <div className="security-section">
        <h4>🔒 Data Protection Analysis</h4>
        <div className="analysis-grid">
          <div className="analysis-stat">
            <span className="stat-label">PII Fields Detected</span>
            <span
              className={`stat-value ${report.data_exposure?.pii_fields_detected?.length > 0 ? "warning" : "positive"}`}
            >
              {report.data_exposure?.pii_fields_detected?.length || 0}
            </span>
          </div>
          <div className="analysis-stat">
            <span className="stat-label">Sensitive Data Fields</span>
            <span
              className={`stat-value ${report.data_exposure?.sensitive_data_fields?.length > 0 ? "warning" : "positive"}`}
            >
              {report.data_exposure?.sensitive_data_fields?.length || 0}
            </span>
          </div>
          <div className="analysis-stat">
            <span className="stat-label">Unencrypted Sensitive Data</span>
            <span
              className={`stat-value ${report.data_exposure?.unencrypted_sensitive_data ? "negative" : "positive"}`}
            >
              {report.data_exposure?.unencrypted_sensitive_data
                ? "✗ Yes"
                : "✓ No"}
            </span>
          </div>
          <div className="analysis-stat">
            <span className="stat-label">Issues Found</span>
            <span className="stat-value">
              {report.data_exposure?.issues?.length || 0}
            </span>
          </div>
        </div>

        {/* PII Fields Details */}
        {report.data_exposure?.pii_fields_detected &&
          report.data_exposure.pii_fields_detected.length > 0 && (
            <div className="pii-details">
              <h5>Detected PII Fields</h5>
              <div className="pii-list">
                {report.data_exposure.pii_fields_detected
                  .slice(0, 5)
                  .map((pii, idx) => (
                    <div key={idx} className="pii-item">
                      <span className="pii-type">{pii.type}</span>
                      <span className="pii-field">
                        {pii.schema}.{pii.field}
                      </span>
                    </div>
                  ))}
                {report.data_exposure.pii_fields_detected.length > 5 && (
                  <div className="pii-more">
                    +{report.data_exposure.pii_fields_detected.length - 5} more
                  </div>
                )}
              </div>
            </div>
          )}
      </div>

      {/* OWASP Compliance */}
      <div className="security-section">
        <h4>📋 OWASP API Security Top 10 Compliance</h4>
        <div className="owasp-compliance">
          <div className="compliance-stats">
            <div className="compliance-stat">
              <span className="compliance-percentage">
                {report.owasp_compliance?.compliance_percentage?.toFixed(0) ||
                  0}
                %
              </span>
              <span className="compliance-label">Compliant</span>
            </div>
            <div className="compliance-breakdown">
              <div className="compliance-item">
                <span className="compliance-icon positive">✓</span>
                <span>
                  {report.owasp_compliance?.compliant_categories?.length || 0}{" "}
                  Compliant
                </span>
              </div>
              <div className="compliance-item">
                <span className="compliance-icon negative">✗</span>
                <span>
                  {report.owasp_compliance?.non_compliant_categories?.length ||
                    0}{" "}
                  Non-Compliant
                </span>
              </div>
            </div>
          </div>

          {/* Compliant Categories */}
          {report.owasp_compliance?.compliant_categories?.length > 0 && (
            <div className="owasp-category-list">
              <h5>✓ Compliant Categories</h5>
              <div className="category-tags">
                {report.owasp_compliance.compliant_categories.map(
                  (cat, idx) => (
                    <span key={idx} className="category-tag compliant">
                      {cat.replace(/_/g, " ")}
                    </span>
                  ),
                )}
              </div>
            </div>
          )}

          {/* Non-Compliant Categories */}
          {report.owasp_compliance?.non_compliant_categories?.length > 0 && (
            <div className="owasp-category-list">
              <h5>✗ Non-Compliant Categories</h5>
              <div className="category-tags">
                {report.owasp_compliance.non_compliant_categories.map(
                  (cat, idx) => (
                    <span key={idx} className="category-tag non-compliant">
                      {cat.replace(/_/g, " ")}
                    </span>
                  ),
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Issue Summary */}
      <div className="security-section">
        <h4>🔍 Issue Summary</h4>
        <div className="issue-summary">
          <div className="severity-badge critical">
            <span className="severity-count">
              {issueCountBySeverity(report.all_issues, "critical")}
            </span>
            <span className="severity-label">Critical</span>
          </div>
          <div className="severity-badge high">
            <span className="severity-count">
              {issueCountBySeverity(report.all_issues, "high")}
            </span>
            <span className="severity-label">High</span>
          </div>
          <div className="severity-badge medium">
            <span className="severity-count">
              {issueCountBySeverity(report.all_issues, "medium")}
            </span>
            <span className="severity-label">Medium</span>
          </div>
          <div className="severity-badge low">
            <span className="severity-count">
              {issueCountBySeverity(report.all_issues, "low")}
            </span>
            <span className="severity-label">Low</span>
          </div>
          <div className="severity-badge info">
            <span className="severity-count">
              {issueCountBySeverity(report.all_issues, "info")}
            </span>
            <span className="severity-label">Info</span>
          </div>
        </div>
      </div>

      {/* Metadata */}
      <div className="security-metadata">
        <span className="metadata-item">
          Generated: {new Date(report.generated_at).toLocaleString()}
        </span>
        <span className="metadata-item">Spec Hash: {report.spec_hash}</span>
      </div>
    </div>
  );
};

export default SecurityReport;
