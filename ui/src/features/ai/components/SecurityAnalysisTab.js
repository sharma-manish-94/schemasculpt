/**
 * SecurityAnalysisTab Component
 * Multi-agent security analysis for OpenAPI specifications
 */

import React, { useState } from "react";
import { runSecurityAnalysis } from "../../../api/securityService";
import { useSpecStore } from "../../../store/specStore";
import { getSecuritySuggestions } from "../../../utils/suggestionGrouping";
import SecurityReport from "./SecurityReport";
import SecurityIssuesList from "./SecurityIssuesList";
import AdvancedSecurityAudit from "../../../components/security/AdvancedSecurityAudit";

const SecurityAnalysisTab = ({ specContent }) => {
  const { sessionId, suggestions } = useSpecStore();
  const [analyzing, setAnalyzing] = useState(false);
  const [report, setReport] = useState(null);
  const [error, setError] = useState(null);
  const [cached, setCached] = useState(false);
  const [activeView, setActiveView] = useState("overview"); // 'overview', 'issues', 'recommendations', 'attack-chains'

  const handleAnalyze = async (forceRefresh = false) => {
    if (!specContent || specContent.trim() === "") {
      setError("No specification content to analyze");
      return;
    }

    setAnalyzing(true);
    setError(null);
    setReport(null);

    try {
      // Get security-related validation suggestions to provide context
      const securitySuggestions = suggestions
        ? getSecuritySuggestions(suggestions)
        : null;

      console.log(
        `Running security analysis with ${securitySuggestions?.length || 0} security-related validation suggestions`,
      );

      const result = await runSecurityAnalysis(
        specContent,
        forceRefresh,
        securitySuggestions,
      );

      if (result.success) {
        setReport(result.report);
        setCached(result.cached);
        setActiveView("overview");
      } else {
        setError(result.error || "Security analysis failed");
      }
    } catch (err) {
      setError(err.message || "An unexpected error occurred");
    } finally {
      setAnalyzing(false);
    }
  };

  const getRiskLevelColor = (riskLevel) => {
    const colors = {
      critical: "#dc2626",
      high: "#ea580c",
      medium: "#f59e0b",
      low: "#10b981",
      info: "#3b82f6",
    };
    return colors[riskLevel?.toLowerCase()] || "#6b7280";
  };

  const getScoreColor = (score) => {
    if (score >= 80) return "#10b981"; // green
    if (score >= 60) return "#f59e0b"; // amber
    if (score >= 40) return "#ea580c"; // orange
    return "#dc2626"; // red
  };

  return (
    <div className="security-analysis-tab">
      <div className="security-header">
        <h3>Security Analysis</h3>
        <p className="security-description">
          Comprehensive multi-agent security analysis covering OWASP API
          Security Top 10 2023
        </p>
      </div>

      <div className="security-actions">
        <button
          className="btn-primary"
          onClick={() => handleAnalyze(false)}
          disabled={analyzing || !specContent}
        >
          {analyzing ? "Analyzing..." : "Run Security Analysis"}
        </button>

        {report && (
          <button
            className="btn-secondary"
            onClick={() => handleAnalyze(true)}
            disabled={analyzing}
          >
            Refresh Analysis
          </button>
        )}
      </div>

      {error && (
        <div className="security-error">
          <span className="error-icon">⚠️</span>
          <span>{error}</span>
        </div>
      )}

      {cached && (
        <div className="security-cache-notice">
          <span className="cache-icon">📦</span>
          <span>Using cached results (24hr TTL)</span>
        </div>
      )}

      {report && (
        <div className="security-results">
          {/* View Tabs */}
          <div className="security-view-tabs">
            <button
              className={`view-tab ${activeView === "overview" ? "active" : ""}`}
              onClick={() => setActiveView("overview")}
            >
              Overview
            </button>
            <button
              className={`view-tab ${activeView === "issues" ? "active" : ""}`}
              onClick={() => setActiveView("issues")}
            >
              Issues ({report.all_issues?.length || 0})
            </button>
            <button
              className={`view-tab ${activeView === "recommendations" ? "active" : ""}`}
              onClick={() => setActiveView("recommendations")}
            >
              Recommendations
            </button>
            <button
              className={`view-tab ${activeView === "attack-chains" ? "active" : ""}`}
              onClick={() => setActiveView("attack-chains")}
            >
              ⚔️ Attack Chains
            </button>
          </div>

          {/* Overview View */}
          {activeView === "overview" && (
            <div className="security-overview">
              {/* Score Card */}
              <div className="security-score-card">
                <div className="score-main">
                  <div
                    className="score-circle"
                    style={{ borderColor: getScoreColor(report.overall_score) }}
                  >
                    <span className="score-value">{report.overall_score}</span>
                    <span className="score-max">/100</span>
                  </div>
                  <div className="score-details">
                    <h4>Overall Security Score</h4>
                    <div
                      className="risk-badge"
                      style={{
                        backgroundColor: getRiskLevelColor(report.risk_level),
                      }}
                    >
                      {report.risk_level?.toUpperCase()} RISK
                    </div>
                  </div>
                </div>
              </div>

              {/* Executive Summary */}
              <div className="executive-summary">
                <h4>Executive Summary</h4>
                <p>{report.executive_summary}</p>
              </div>

              {/* Security Report Component */}
              <SecurityReport report={report} />
            </div>
          )}

          {/* Issues View */}
          {activeView === "issues" && (
            <SecurityIssuesList issues={report.all_issues || []} />
          )}

          {/* Recommendations View */}
          {activeView === "recommendations" && (
            <div className="security-recommendations">
              <h4>Security Recommendations</h4>

              {/* Authentication Recommendations */}
              {report.authentication?.recommendations?.length > 0 && (
                <div className="recommendation-section">
                  <h5>🔐 Authentication</h5>
                  <ul>
                    {report.authentication.recommendations.map((rec, idx) => (
                      <li key={`auth-rec-${idx}`}>{rec}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Authorization Recommendations */}
              {report.authorization?.recommendations?.length > 0 && (
                <div className="recommendation-section">
                  <h5>🛡️ Authorization</h5>
                  <ul>
                    {report.authorization.recommendations.map((rec, idx) => (
                      <li key={`authz-rec-${idx}`}>{rec}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Data Protection Recommendations */}
              {report.data_exposure?.recommendations?.length > 0 && (
                <div className="recommendation-section">
                  <h5>🔒 Data Protection</h5>
                  <ul>
                    {report.data_exposure.recommendations.map((rec, idx) => (
                      <li key={`data-rec-${idx}`}>{rec}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* OWASP Compliance Recommendations */}
              {report.owasp_compliance?.recommendations?.length > 0 && (
                <div className="recommendation-section">
                  <h5>📋 OWASP Compliance</h5>
                  <ul>
                    {report.owasp_compliance.recommendations.map((rec, idx) => (
                      <li key={`owasp-rec-${idx}`}>{rec}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {/* Attack Chains View */}
          {activeView === "attack-chains" && (
            <div className="attack-chains-view">
              <AdvancedSecurityAudit sessionId={sessionId} />
            </div>
          )}
        </div>
      )}

      {!report && !analyzing && !error && (
        <div className="security-empty-state">
          <div className="empty-icon">🔐</div>
          <p>
            Run a security analysis to identify vulnerabilities and compliance
            issues
          </p>
          <ul className="security-features">
            <li>✓ Multi-agent security analysis</li>
            <li>✓ OWASP API Security Top 10 compliance</li>
            <li>✓ Authentication & authorization checks</li>
            <li>✓ PII & data exposure detection</li>
            <li>✓ Actionable remediation guidance</li>
          </ul>
        </div>
      )}
    </div>
  );
};

export default SecurityAnalysisTab;
