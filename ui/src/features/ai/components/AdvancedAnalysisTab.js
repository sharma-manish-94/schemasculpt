/**
 * AdvancedAnalysisTab Component
 * Displays results from 4 advanced architectural analyzers:
 * 1. Taint Analysis - Data security
 * 2. Authorization Matrix - Access control
 * 3. Schema Similarity - Code quality
 * 4. Zombie API Detection - Maintenance
 */

import React, { useState } from "react";
import { useSpecStore } from "../../../store/specStore";
import {
  runComprehensiveAnalysis,
  runTaintAnalysis,
  interpretTaintAnalysis,
  runAuthzMatrixAnalysis,
  interpretAuthzMatrix,
  runSchemaSimilarityAnalysis,
  interpretSchemaSimilarity,
  runZombieApiDetection,
  interpretZombieApis,
} from "../../../api/analysisService";
import "./AdvancedAnalysisTab.css";

const AdvancedAnalysisTab = ({ specContent }) => {
  const { sessionId } = useSpecStore();
  const [analyzing, setAnalyzing] = useState(false);
  const [activeAnalyzer, setActiveAnalyzer] = useState("comprehensive"); // 'comprehensive', 'taint', 'authz', 'similarity', 'zombie'
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState("overview"); // 'overview', 'details'

  const handleRunComprehensiveAnalysis = async () => {
    if (!specContent || !sessionId) {
      setError("No specification content or session");
      return;
    }

    setAnalyzing(true);
    setError(null);
    setResults(null);
    setActiveAnalyzer("comprehensive");

    try {
      const result = await runComprehensiveAnalysis(sessionId, specContent);

      if (result.success) {
        setResults(result);
      } else {
        setError(result.error || "Comprehensive analysis failed");
      }
    } catch (err) {
      setError(err.message || "An unexpected error occurred");
    } finally {
      setAnalyzing(false);
    }
  };

  const handleRunSpecificAnalyzer = async (analyzerType) => {
    if (!specContent || !sessionId) {
      setError("No specification content or session");
      return;
    }

    setAnalyzing(true);
    setError(null);
    setResults(null);
    setActiveAnalyzer(analyzerType);

    try {
      let rawResult, interpretation;

      switch (analyzerType) {
        case "taint":
          rawResult = await runTaintAnalysis(sessionId);
          if (rawResult.success) {
            interpretation = await interpretTaintAnalysis(
              rawResult.data,
              specContent,
            );
          }
          break;
        case "authz":
          rawResult = await runAuthzMatrixAnalysis(sessionId);
          if (rawResult.success) {
            interpretation = await interpretAuthzMatrix(
              rawResult.data,
              specContent,
            );
          }
          break;
        case "similarity":
          rawResult = await runSchemaSimilarityAnalysis(sessionId);
          if (rawResult.success) {
            interpretation = await interpretSchemaSimilarity(
              rawResult.data,
              specContent,
            );
          }
          break;
        case "zombie":
          rawResult = await runZombieApiDetection(sessionId);
          if (rawResult.success) {
            interpretation = await interpretZombieApis(
              rawResult.data,
              specContent,
            );
          }
          break;
        default:
          throw new Error("Unknown analyzer type");
      }

      if (rawResult.success && interpretation.success) {
        setResults({
          success: true,
          raw_results: rawResult.data,
          interpretation: interpretation.interpretation,
        });
      } else {
        setError(rawResult.error || interpretation.error || "Analysis failed");
      }
    } catch (err) {
      setError(err.message || "An unexpected error occurred");
    } finally {
      setAnalyzing(false);
    }
  };

  const getHealthColor = (score) => {
    if (score >= 80) return "#10b981"; // green
    if (score >= 60) return "#f59e0b"; // amber
    if (score >= 40) return "#ea580c"; // orange
    return "#dc2626"; // red
  };

  const getRiskColor = (riskLevel) => {
    const colors = {
      CRITICAL: "#dc2626",
      HIGH: "#ea580c",
      MEDIUM: "#f59e0b",
      LOW: "#10b981",
      INFO: "#3b82f6",
    };
    return colors[riskLevel?.toUpperCase()] || "#6b7280";
  };

  return (
    <div className="advanced-analysis-tab">
      <div className="analysis-header">
        <h3>🔬 Advanced Architectural Analysis</h3>
        <p className="analysis-description">
          Pre-calculated complex facts enabling instant expert-level security
          and governance insights
        </p>
      </div>

      <div className="analyzer-buttons">
        <button
          className={`btn-analyzer ${activeAnalyzer === "comprehensive" ? "active" : ""}`}
          onClick={handleRunComprehensiveAnalysis}
          disabled={analyzing || !specContent}
        >
          {analyzing && activeAnalyzer === "comprehensive" ? "⏳" : "🎯"}{" "}
          Comprehensive Analysis
        </button>

        <div className="analyzer-grid">
          <button
            className={`btn-analyzer-card ${activeAnalyzer === "taint" ? "active" : ""}`}
            onClick={() => handleRunSpecificAnalyzer("taint")}
            disabled={analyzing || !specContent}
          >
            <div className="analyzer-icon">🔍</div>
            <div className="analyzer-name">Taint Analysis</div>
            <div className="analyzer-desc">Track sensitive data flow</div>
          </button>

          <button
            className={`btn-analyzer-card ${activeAnalyzer === "authz" ? "active" : ""}`}
            onClick={() => handleRunSpecificAnalyzer("authz")}
            disabled={analyzing || !specContent}
          >
            <div className="analyzer-icon">🛡️</div>
            <div className="analyzer-name">Authz Matrix</div>
            <div className="analyzer-desc">RBAC analysis</div>
          </button>

          <button
            className={`btn-analyzer-card ${activeAnalyzer === "similarity" ? "active" : ""}`}
            onClick={() => handleRunSpecificAnalyzer("similarity")}
            disabled={analyzing || !specContent}
          >
            <div className="analyzer-icon">📦</div>
            <div className="analyzer-name">Schema Similarity</div>
            <div className="analyzer-desc">Find duplicates</div>
          </button>

          <button
            className={`btn-analyzer-card ${activeAnalyzer === "zombie" ? "active" : ""}`}
            onClick={() => handleRunSpecificAnalyzer("zombie")}
            disabled={analyzing || !specContent}
          >
            <div className="analyzer-icon">🧟</div>
            <div className="analyzer-name">Zombie API</div>
            <div className="analyzer-desc">Dead code detection</div>
          </button>
        </div>
      </div>

      {error && (
        <div className="analysis-error">
          <span className="error-icon">⚠️</span>
          <span>{error}</span>
        </div>
      )}

      {analyzing && (
        <div className="analysis-loading">
          <div className="loading-spinner"></div>
          <p>Running {activeAnalyzer} analysis...</p>
        </div>
      )}

      {results && !analyzing && (
        <div className="analysis-results">
          {/* Tabs */}
          <div className="results-tabs">
            <button
              className={`tab ${activeTab === "overview" ? "active" : ""}`}
              onClick={() => setActiveTab("overview")}
            >
              Overview
            </button>
            <button
              className={`tab ${activeTab === "details" ? "active" : ""}`}
              onClick={() => setActiveTab("details")}
            >
              Detailed Results
            </button>
          </div>

          {/* Overview Tab */}
          {activeTab === "overview" && results.interpretation && (
            <div className="overview-content">
              {/* Comprehensive Analysis Results */}
              {activeAnalyzer === "comprehensive" && (
                <div className="comprehensive-results">
                  {/* Health Score Dashboard */}
                  <div className="health-dashboard">
                    <div className="main-score-card">
                      <div
                        className="score-circle-large"
                        style={{
                          borderColor: getHealthColor(
                            results.interpretation.overall_health_score,
                          ),
                        }}
                      >
                        <span className="score-value">
                          {results.interpretation.overall_health_score}
                        </span>
                        <span className="score-label">Health Score</span>
                      </div>
                      <div
                        className="risk-badge-large"
                        style={{
                          backgroundColor: getRiskColor(
                            results.interpretation.risk_level,
                          ),
                        }}
                      >
                        {results.interpretation.risk_level} RISK
                      </div>
                    </div>

                    {/* Breakdown Scores */}
                    {results.interpretation.health_breakdown && (
                      <div className="score-breakdown">
                        <ScoreCard
                          title="Security"
                          score={
                            results.interpretation.health_breakdown
                              .security_score
                          }
                          icon="🔒"
                        />
                        <ScoreCard
                          title="Access Control"
                          score={
                            results.interpretation.health_breakdown
                              .access_control_score
                          }
                          icon="🛡️"
                        />
                        <ScoreCard
                          title="Code Quality"
                          score={
                            results.interpretation.health_breakdown
                              .code_quality_score
                          }
                          icon="✨"
                        />
                        <ScoreCard
                          title="Maintenance"
                          score={
                            results.interpretation.health_breakdown
                              .maintenance_score
                          }
                          icon="🔧"
                        />
                      </div>
                    )}
                  </div>

                  {/* Executive Summary */}
                  <div className="executive-summary-section">
                    <h4>📋 Executive Summary</h4>
                    <p>{results.interpretation.executive_summary}</p>
                  </div>

                  {/* Top 3 Critical Issues */}
                  {results.interpretation.top_3_critical_issues &&
                    results.interpretation.top_3_critical_issues.length > 0 && (
                      <div className="critical-issues-section">
                        <h4>🚨 Top 3 Critical Issues</h4>
                        {results.interpretation.top_3_critical_issues.map(
                          (issue, idx) => (
                            <div key={idx} className="critical-issue-card">
                              <div className="issue-header">
                                <span className="issue-category">
                                  {issue.category}
                                </span>
                                <span
                                  className="issue-urgency"
                                  style={{
                                    backgroundColor: getRiskColor(
                                      issue.urgency,
                                    ),
                                  }}
                                >
                                  {issue.urgency}
                                </span>
                              </div>
                              <div className="issue-content">
                                <h5>{issue.issue}</h5>
                                <p>{issue.business_impact}</p>
                              </div>
                            </div>
                          ),
                        )}
                      </div>
                    )}

                  {/* Action Items */}
                  <div className="action-items-grid">
                    {results.interpretation.immediate_action_items &&
                      results.interpretation.immediate_action_items.length >
                        0 && (
                        <div className="action-section">
                          <h4>⚡ Immediate Actions</h4>
                          <ul>
                            {results.interpretation.immediate_action_items.map(
                              (item, idx) => (
                                <li key={idx}>{item}</li>
                              ),
                            )}
                          </ul>
                        </div>
                      )}

                    {results.interpretation.short_term_roadmap &&
                      results.interpretation.short_term_roadmap.length > 0 && (
                        <div className="action-section">
                          <h4>📅 Short-term Roadmap (1-2 weeks)</h4>
                          <ul>
                            {results.interpretation.short_term_roadmap.map(
                              (item, idx) => (
                                <li key={idx}>{item}</li>
                              ),
                            )}
                          </ul>
                        </div>
                      )}

                    {results.interpretation.long_term_improvements &&
                      results.interpretation.long_term_improvements.length >
                        0 && (
                        <div className="action-section">
                          <h4>🎯 Long-term Improvements</h4>
                          <ul>
                            {results.interpretation.long_term_improvements.map(
                              (item, idx) => (
                                <li key={idx}>{item}</li>
                              ),
                            )}
                          </ul>
                        </div>
                      )}
                  </div>

                  {/* ROI Analysis */}
                  {results.interpretation.roi_analysis && (
                    <div className="roi-section">
                      <h4>💰 ROI Analysis</h4>
                      <p>{results.interpretation.roi_analysis}</p>
                      {results.interpretation.estimated_total_effort && (
                        <p className="effort-estimate">
                          <strong>Estimated Effort:</strong>{" "}
                          {results.interpretation.estimated_total_effort}
                        </p>
                      )}
                    </div>
                  )}
                </div>
              )}

              {/* Specific Analyzer Results */}
              {activeAnalyzer !== "comprehensive" && (
                <SpecificAnalyzerResults
                  analyzerType={activeAnalyzer}
                  interpretation={results.interpretation}
                  getRiskColor={getRiskColor}
                />
              )}
            </div>
          )}

          {/* Details Tab */}
          {activeTab === "details" && (
            <div className="details-content">
              <h4>Raw Analysis Data</h4>
              <pre className="json-data">
                {JSON.stringify(results.raw_results, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}

      {!results && !analyzing && !error && (
        <div className="analysis-empty-state">
          <div className="empty-icon">🔬</div>
          <h3>Advanced Architectural Analysis</h3>
          <p>Run comprehensive analysis to discover:</p>
          <ul className="analysis-features">
            <li>
              🔍 <strong>Taint Analysis:</strong> Track sensitive data leakage
              paths
            </li>
            <li>
              🛡️ <strong>Authz Matrix:</strong> Identify RBAC misconfigurations
              and privilege escalation risks
            </li>
            <li>
              📦 <strong>Schema Similarity:</strong> Find duplicate schemas and
              refactoring opportunities
            </li>
            <li>
              🧟 <strong>Zombie APIs:</strong> Detect unreachable endpoints and
              dead code
            </li>
          </ul>
        </div>
      )}
    </div>
  );
};

// Helper component for score cards
const ScoreCard = ({ title, score, icon }) => {
  const getColor = (s) => {
    if (s >= 80) return "#10b981";
    if (s >= 60) return "#f59e0b";
    if (s >= 40) return "#ea580c";
    return "#dc2626";
  };

  return (
    <div className="score-card">
      <div className="score-icon">{icon}</div>
      <div className="score-info">
        <div className="score-title">{title}</div>
        <div className="score-number" style={{ color: getColor(score) }}>
          {score}/100
        </div>
      </div>
    </div>
  );
};

// Helper component for specific analyzer results
const SpecificAnalyzerResults = ({
  analyzerType,
  interpretation,
  getRiskColor,
}) => {
  switch (analyzerType) {
    case "taint":
      return (
        <TaintAnalysisResults
          interpretation={interpretation}
          getRiskColor={getRiskColor}
        />
      );
    case "authz":
      return (
        <AuthzMatrixResults
          interpretation={interpretation}
          getRiskColor={getRiskColor}
        />
      );
    case "similarity":
      return <SchemaSimilarityResults interpretation={interpretation} />;
    case "zombie":
      return <ZombieApiResults interpretation={interpretation} />;
    default:
      return null;
  }
};

// Taint Analysis Results Component
const TaintAnalysisResults = ({ interpretation, getRiskColor }) => (
  <div className="taint-results">
    <div className="result-header">
      <h3>🔍 Taint Analysis Results</h3>
      <span
        className="risk-badge"
        style={{ backgroundColor: getRiskColor(interpretation.risk_level) }}
      >
        {interpretation.risk_level} RISK
      </span>
    </div>

    <div className="summary-section">
      <h4>Summary</h4>
      <p>{interpretation.executive_summary}</p>
    </div>

    {interpretation.top_issues && interpretation.top_issues.length > 0 && (
      <div className="issues-section">
        <h4>🚨 Data Leakage Issues</h4>
        {interpretation.top_issues.map((issue, idx) => (
          <div key={idx} className="issue-card">
            <div className="issue-header">
              <strong>{issue.endpoint}</strong>
              <span
                className="severity-badge"
                style={{ backgroundColor: getRiskColor(issue.severity) }}
              >
                {issue.severity}
              </span>
            </div>
            <p className="issue-description">{issue.issue}</p>
            <p className="leaked-data">
              <strong>Leaked Data:</strong> {issue.leaked_data}
            </p>
            <p className="attack-scenario">
              <strong>Attack Scenario:</strong> {issue.attack_scenario}
            </p>
            {issue.compliance_impact && (
              <p className="compliance-impact">
                <strong>Compliance:</strong> {issue.compliance_impact}
              </p>
            )}
          </div>
        ))}
      </div>
    )}

    {interpretation.remediation_priorities &&
      interpretation.remediation_priorities.length > 0 && (
        <div className="remediation-section">
          <h4>🔧 Remediation Priorities</h4>
          {interpretation.remediation_priorities.map((item, idx) => (
            <div key={idx} className="remediation-card">
              <div className="priority-badge">{item.priority}</div>
              <div className="remediation-content">
                <p>
                  <strong>{item.action}</strong>
                </p>
                <p className="affected-endpoints">
                  Affects:{" "}
                  {item.endpoints_affected?.join(", ") || "Multiple endpoints"}
                </p>
                <p className="effort">Effort: {item.estimated_effort}</p>
              </div>
            </div>
          ))}
        </div>
      )}
  </div>
);

// Authorization Matrix Results Component
const AuthzMatrixResults = ({ interpretation, getRiskColor }) => (
  <div className="authz-results">
    <div className="result-header">
      <h3>🛡️ Authorization Matrix Analysis</h3>
      <span
        className="risk-badge"
        style={{ backgroundColor: getRiskColor(interpretation.risk_level) }}
      >
        {interpretation.risk_level} RISK
      </span>
    </div>

    <div className="summary-section">
      <h4>Summary</h4>
      <p>{interpretation.executive_summary}</p>
    </div>

    {interpretation.anomalies_detected &&
      interpretation.anomalies_detected.length > 0 && (
        <div className="anomalies-section">
          <h4>⚠️ Security Anomalies Detected</h4>
          {interpretation.anomalies_detected.map((anomaly, idx) => (
            <div key={idx} className="anomaly-card">
              <div className="anomaly-header">
                <span className="anomaly-type">{anomaly.type}</span>
                <span
                  className="severity-badge"
                  style={{ backgroundColor: getRiskColor(anomaly.severity) }}
                >
                  {anomaly.severity}
                </span>
              </div>
              <p className="endpoint">
                <strong>Endpoint:</strong> {anomaly.endpoint}
              </p>
              <p className="issue-description">{anomaly.issue}</p>
              <p className="current-scopes">
                <strong>Current Scopes:</strong>{" "}
                {anomaly.current_scopes?.join(", ") || "None"}
              </p>
              <p className="attack-scenario">
                <strong>Attack:</strong> {anomaly.attack_scenario}
              </p>
              <p className="recommendation">
                <strong>Recommended Scopes:</strong>{" "}
                {anomaly.recommended_scopes?.join(", ") || "N/A"}
              </p>
            </div>
          ))}
        </div>
      )}

    {interpretation.recommendations &&
      interpretation.recommendations.length > 0 && (
        <div className="recommendations-section">
          <h4>💡 Recommendations</h4>
          {interpretation.recommendations.map((rec, idx) => (
            <div key={idx} className="recommendation-card">
              <div className="priority-badge">{rec.priority}</div>
              <p>{rec.recommendation}</p>
              {rec.affected_endpoints && rec.affected_endpoints.length > 0 && (
                <p className="affected">
                  Affects: {rec.affected_endpoints.join(", ")}
                </p>
              )}
            </div>
          ))}
        </div>
      )}
  </div>
);

// Schema Similarity Results Component
const SchemaSimilarityResults = ({ interpretation }) => (
  <div className="similarity-results">
    <div className="result-header">
      <h3>📦 Schema Similarity Analysis</h3>
      {interpretation.code_health_score && (
        <div className="health-badge">
          Code Health: {interpretation.code_health_score}/100
        </div>
      )}
    </div>

    <div className="summary-section">
      <h4>Summary</h4>
      <p>{interpretation.executive_summary}</p>
      {interpretation.potential_savings && (
        <p className="savings">
          <strong>Potential Savings:</strong> {interpretation.potential_savings}
        </p>
      )}
    </div>

    {interpretation.refactoring_opportunities &&
      interpretation.refactoring_opportunities.length > 0 && (
        <div className="refactoring-section">
          <h4>🔄 Refactoring Opportunities</h4>
          {interpretation.refactoring_opportunities.map((opp, idx) => (
            <div key={idx} className="refactoring-card">
              <div className="schemas">
                <strong>Schemas:</strong>{" "}
                {opp.schema_names?.join(", ") || "N/A"}
                <span className="similarity-score">
                  {Math.round(opp.similarity_score * 100)}% similar
                </span>
              </div>
              <p className="issue">{opp.issue}</p>
              <p className="strategy">
                <strong>Strategy:</strong> {opp.refactoring_strategy}
              </p>
              <div className="implementation-steps">
                <strong>Implementation Steps:</strong>
                <ol>
                  {opp.implementation_steps?.map((step, sIdx) => (
                    <li key={sIdx}>{step}</li>
                  ))}
                </ol>
              </div>
              <div className="metadata">
                <span className="effort">Effort: {opp.estimated_effort}</span>
                <span className="risk">
                  Breaking Change Risk: {opp.breaking_change_risk}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

    {interpretation.quick_wins && interpretation.quick_wins.length > 0 && (
      <div className="quick-wins-section">
        <h4>⚡ Quick Wins</h4>
        {interpretation.quick_wins.map((win, idx) => (
          <div key={idx} className="quick-win-card">
            <p>
              <strong>Schemas:</strong> {win.schemas?.join(", ")}
            </p>
            <p className="effort">Effort: {win.effort}</p>
            <p className="impact">{win.impact}</p>
          </div>
        ))}
      </div>
    )}
  </div>
);

// Zombie API Results Component
const ZombieApiResults = ({ interpretation }) => (
  <div className="zombie-results">
    <div className="result-header">
      <h3>🧟 Zombie API Detection</h3>
      {interpretation.code_health_score && (
        <div className="health-badge">
          Code Health: {interpretation.code_health_score}/100
        </div>
      )}
    </div>

    <div className="summary-section">
      <h4>Summary</h4>
      <p>{interpretation.executive_summary}</p>
      {interpretation.maintenance_burden && (
        <p className="burden">
          <strong>Maintenance Burden:</strong>{" "}
          {interpretation.maintenance_burden}
        </p>
      )}
    </div>

    {interpretation.shadowed_endpoint_analysis &&
      interpretation.shadowed_endpoint_analysis.length > 0 && (
        <div className="shadowed-section">
          <h4>👻 Shadowed Endpoints (Unreachable)</h4>
          {interpretation.shadowed_endpoint_analysis.map((item, idx) => (
            <div key={idx} className="zombie-card">
              <p>
                <strong>Shadowed:</strong> {item.shadowed_path}
              </p>
              <p>
                <strong>By:</strong> {item.shadowing_path}
              </p>
              <p className="reason">{item.reason}</p>
              <p className="recommendation">
                <strong>Fix:</strong> {item.recommendation} -{" "}
                {item.fix_instructions}
              </p>
              <p className="breaking">
                Breaking Change: {item.breaking_change}
              </p>
            </div>
          ))}
        </div>
      )}

    {interpretation.orphaned_operation_analysis &&
      interpretation.orphaned_operation_analysis.length > 0 && (
        <div className="orphaned-section">
          <h4>💀 Orphaned Operations</h4>
          {interpretation.orphaned_operation_analysis.map((item, idx) => (
            <div key={idx} className="zombie-card">
              <p>
                <strong>Operation:</strong> {item.operation}
              </p>
              <p className="reason">{item.reason}</p>
              <p className="recommendation">
                <strong>Recommendation:</strong> {item.recommendation}
              </p>
              <p className="rationale">{item.rationale}</p>
            </div>
          ))}
        </div>
      )}

    {interpretation.cleanup_priorities &&
      interpretation.cleanup_priorities.length > 0 && (
        <div className="cleanup-section">
          <h4>🧹 Cleanup Priorities</h4>
          {interpretation.cleanup_priorities.map((item, idx) => (
            <div key={idx} className="cleanup-card">
              <div className="priority-badge">{item.priority}</div>
              <p>{item.action}</p>
              <p className="affected">
                Affects: {item.affected_endpoints?.join(", ")}
              </p>
              <p className="effort">Effort: {item.estimated_effort}</p>
            </div>
          ))}
        </div>
      )}
  </div>
);

export default AdvancedAnalysisTab;
