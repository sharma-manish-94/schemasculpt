/**
 * Attack Path Report Component
 *
 * Displays the results of the AI-powered attack path simulation.
 * Shows multi-step attack chains, executive summary, and remediation roadmap.
 */

import React, { useState } from "react";
import {
  formatSeverity,
  formatRiskLevel,
  getSecurityScoreColor,
} from "../../api/attackPathService";
import "./AttackPathReport.css";

const AttackPathReport = ({ report, onClose }) => {
  const [selectedChain, setSelectedChain] = useState(null);
  const [activeTab, setActiveTab] = useState("overview");

  if (!report) return null;

  const {
    executive_summary,
    risk_level,
    overall_security_score,
    critical_chains = [],
    high_priority_chains = [],
    all_chains = [],
    top_3_risks = [],
    immediate_actions = [],
    short_term_actions = [],
    long_term_actions = [],
    total_chains_found,
    total_vulnerabilities,
    vulnerabilities_in_chains,
    isolated_vulnerabilities,
  } = report;

  const riskInfo = formatRiskLevel(risk_level);
  const scoreColor = getSecurityScoreColor(overall_security_score);

  const renderAttackChain = (chain) => {
    // Safe defaults for missing fields
    const likelihood = chain.likelihood ?? 0.7;
    const complexity = chain.complexity || "Medium";
    const steps = Array.isArray(chain.steps) ? chain.steps : [];

    return (
      <div
        key={chain.chain_id || chain.name}
        className="attack-chain-card"
        onClick={() => setSelectedChain(chain)}
      >
        <div className="attack-chain-header">
          <div className="attack-chain-title">
            <span
              className={`severity-badge severity-${(
                chain.severity || "medium"
              ).toLowerCase()}`}
            >
              {formatSeverity(chain.severity || "MEDIUM").label}
            </span>
            <h3>{chain.name || "Unknown Attack"}</h3>
          </div>
          <div className="attack-chain-meta">
            <span className="chain-complexity">Complexity: {complexity}</span>
            <span className="chain-likelihood">
              Likelihood: {(likelihood * 100).toFixed(0)}%
            </span>
          </div>
        </div>

        <p className="attack-goal">
          {chain.attack_goal || "No description available"}
        </p>
        <p className="business-impact">
          {chain.business_impact || "Impact unknown"}
        </p>

        <div className="attack-steps-preview">
          <strong>{steps.length} Steps:</strong>
          {steps.map((step, idx) => {
            // Handle both string steps and object steps
            if (typeof step === "string") {
              return (
                <span key={idx} className="step-preview">
                  {step}
                </span>
              );
            }
            const method = step.http_method || "API";
            const endpoint = step.endpoint || "call";
            return (
              <span key={idx} className="step-preview">
                {idx + 1}. {method} {endpoint}
              </span>
            );
          })}
        </div>
      </div>
    );
  };

  const renderChainDetails = (chain) => {
    // Safe defaults
    const likelihood = chain.likelihood ?? 0.7;
    const impactScore = chain.impact_score ?? 7.5;
    const steps = Array.isArray(chain.steps) ? chain.steps : [];
    const remediationSteps = Array.isArray(chain.remediation_steps)
      ? chain.remediation_steps
      : [];

    return (
      <div className="chain-details-page">
        <div className="chain-details-header">
          <button
            onClick={() => setSelectedChain(null)}
            className="back-button"
          >
            ← Back to All Chains
          </button>
          <h2>{chain.name || "Attack Chain Details"}</h2>
        </div>

        <div className="chain-details-content">
          <div className="chain-overview">
            <div className="overview-item">
              <label>Attack Goal:</label>
              <p>{chain.attack_goal || "No description available"}</p>
            </div>
            <div className="overview-item">
              <label>Business Impact:</label>
              <p>{chain.business_impact || "Impact not specified"}</p>
            </div>
            <div className="overview-item">
              <label>Attacker Profile:</label>
              <p>{chain.attacker_profile || "Authenticated User"}</p>
            </div>
            <div className="overview-metrics">
              <div className="metric">
                <span
                  className={`severity-badge severity-${(
                    chain.severity || "medium"
                  ).toLowerCase()}`}
                >
                  {chain.severity || "MEDIUM"}
                </span>
              </div>
              <div className="metric">
                <label>Complexity:</label>
                <span>{chain.complexity || "Medium"}</span>
              </div>
              <div className="metric">
                <label>Likelihood:</label>
                <span>{(likelihood * 100).toFixed(0)}%</span>
              </div>
              <div className="metric">
                <label>Impact:</label>
                <span>{impactScore.toFixed(1)}/10</span>
              </div>
            </div>
          </div>

          <div className="attack-steps-detailed">
            <h3>Attack Steps</h3>
            {steps.map((step, idx) => {
              // Handle both string steps and object steps
              if (typeof step === "string") {
                return (
                  <div key={idx} className="attack-step">
                    <div className="step-number">{idx + 1}</div>
                    <div className="step-content">
                      <p className="step-description">{step}</p>
                    </div>
                  </div>
                );
              }

              // Handle object steps with safe defaults
              const stepNumber = step.step_number || idx + 1;
              const httpMethod = step.http_method || "API";
              const endpoint = step.endpoint || "/";
              const description = step.description || "Step not described";
              const stepType = step.step_type || "EXPLOIT";

              return (
                <div key={idx} className="attack-step">
                  <div className="step-number">{stepNumber}</div>
                  <div className="step-content">
                    <div className="step-header">
                      <span className="step-type">
                        {stepType.replace("_", " ").toUpperCase()}
                      </span>
                      <span className="step-endpoint">
                        <code>
                          {httpMethod} {endpoint}
                        </code>
                      </span>
                    </div>
                    <p className="step-description">{description}</p>

                    {step.technical_detail && (
                      <p className="step-technical">
                        <strong>How to exploit:</strong> {step.technical_detail}
                      </p>
                    )}

                    {step.information_gained &&
                      step.information_gained.length > 0 && (
                        <div className="step-gains">
                          <strong>Information Gained:</strong>
                          <ul>
                            {step.information_gained.map((info, i) => (
                              <li key={i}>{info}</li>
                            ))}
                          </ul>
                        </div>
                      )}

                    {step.example_request && (
                      <details className="step-example">
                        <summary>Example Exploit</summary>
                        <pre>{step.example_request}</pre>
                      </details>
                    )}
                  </div>
                </div>
              );
            })}
          </div>

          <div className="remediation-section">
            <h3>How to Fix</h3>
            {chain.remediation_priority && (
              <div className="remediation-priority">
                Priority: <strong>{chain.remediation_priority}</strong>
              </div>
            )}
            {remediationSteps.length > 0 ? (
              <ol className="remediation-steps">
                {remediationSteps.map((step, idx) => (
                  <li key={idx}>{step}</li>
                ))}
              </ol>
            ) : (
              <p>No remediation steps specified.</p>
            )}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="attack-path-report">
      <div className="report-header">
        <div className="header-left">
          <h1>Attack Path Simulation Report</h1>
          <div className="header-badges">
            <div
              className="risk-badge"
              style={{
                backgroundColor: riskInfo.bgColor,
                color: riskInfo.color,
              }}
            >
              {riskInfo.label}
            </div>
            <div className="security-score" style={{ borderColor: scoreColor }}>
              <div className="score-label">Security Score</div>
              <div className="score-value" style={{ color: scoreColor }}>
                {overall_security_score.toFixed(1)}/100
              </div>
            </div>
          </div>
        </div>
        <button onClick={onClose} className="close-report-btn">
          Close Report
        </button>
      </div>

      <div className="report-tabs">
        <button
          className={activeTab === "overview" ? "active" : ""}
          onClick={() => setActiveTab("overview")}
        >
          Overview
        </button>
        <button
          className={activeTab === "chains" ? "active" : ""}
          onClick={() => setActiveTab("chains")}
        >
          Attack Chains ({total_chains_found})
        </button>
        <button
          className={activeTab === "remediation" ? "active" : ""}
          onClick={() => setActiveTab("remediation")}
        >
          Remediation
        </button>
      </div>

      <div className="report-content">
        {activeTab === "overview" && (
          <div className="overview-tab">
            <div className="executive-summary">
              <h2>Executive Summary</h2>
              <div className="summary-text">{executive_summary}</div>
            </div>

            <div className="statistics-grid">
              <div className="stat-card">
                <div className="stat-value">{total_chains_found}</div>
                <div className="stat-label">Attack Chains Found</div>
              </div>
              <div className="stat-card">
                <div className="stat-value">{total_vulnerabilities}</div>
                <div className="stat-label">Total Vulnerabilities</div>
              </div>
              <div className="stat-card">
                <div className="stat-value">{vulnerabilities_in_chains}</div>
                <div className="stat-label">In Chains</div>
              </div>
              <div className="stat-card">
                <div className="stat-value">{isolated_vulnerabilities}</div>
                <div className="stat-label">Isolated</div>
              </div>
            </div>

            {top_3_risks.length > 0 && (
              <div className="top-risks">
                <h2>Top 3 Risks</h2>
                <ol className="risks-list">
                  {top_3_risks.map((risk, idx) => (
                    <li key={idx}>{risk}</li>
                  ))}
                </ol>
              </div>
            )}
          </div>
        )}

        {activeTab === "chains" && (
          <div className="chains-tab">
            {selectedChain ? (
              renderChainDetails(selectedChain)
            ) : (
              <>
                {critical_chains.length > 0 && (
                  <div className="chains-section">
                    <h2>Critical Attack Chains</h2>
                    <div className="chains-grid">
                      {critical_chains.map(renderAttackChain)}
                    </div>
                  </div>
                )}

                {high_priority_chains.length > 0 && (
                  <div className="chains-section">
                    <h2>High Priority Attack Chains</h2>
                    <div className="chains-grid">
                      {high_priority_chains.map(renderAttackChain)}
                    </div>
                  </div>
                )}

                {all_chains.length === 0 && (
                  <div className="no-chains">
                    <p>
                      No attack chains discovered. Individual vulnerabilities
                      may exist but cannot be easily chained together.
                    </p>
                  </div>
                )}
              </>
            )}
          </div>
        )}

        {activeTab === "remediation" && (
          <div className="remediation-tab">
            {immediate_actions.length > 0 && (
              <div className="remediation-section">
                <h2>🚨 Immediate Actions (Fix Now)</h2>
                <ul className="action-list immediate">
                  {immediate_actions.map((action, idx) => (
                    <li key={idx}>{action}</li>
                  ))}
                </ul>
              </div>
            )}

            {short_term_actions.length > 0 && (
              <div className="remediation-section">
                <h2>⚠️ Short-Term Actions (1-2 Weeks)</h2>
                <ul className="action-list short-term">
                  {short_term_actions.map((action, idx) => (
                    <li key={idx}>{action}</li>
                  ))}
                </ul>
              </div>
            )}

            {long_term_actions.length > 0 && (
              <div className="remediation-section">
                <h2>🏗️ Long-Term Improvements (Architectural)</h2>
                <ul className="action-list long-term">
                  {long_term_actions.map((action, idx) => (
                    <li key={idx}>{action}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default AttackPathReport;
