/**
 * Attack Path Report Component
 *
 * Displays the results of the AI-powered attack path simulation.
 * Shows multi-step attack chains, executive summary, and remediation roadmap.
 */

import React, { useState } from 'react';
import { formatSeverity, formatRiskLevel, getSecurityScoreColor } from '../../api/attackPathService';
import './AttackPathReport.css';

const AttackPathReport = ({ report, onClose }) => {
  const [selectedChain, setSelectedChain] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');

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
    isolated_vulnerabilities
  } = report;

  const riskInfo = formatRiskLevel(risk_level);
  const scoreColor = getSecurityScoreColor(overall_security_score);

  const renderAttackChain = (chain) => (
    <div
      key={chain.chain_id}
      className="attack-chain-card"
      onClick={() => setSelectedChain(chain)}
    >
      <div className="attack-chain-header">
        <div className="attack-chain-title">
          <span className={`severity-badge severity-${chain.severity.toLowerCase()}`}>
            {formatSeverity(chain.severity).label}
          </span>
          <h3>{chain.name}</h3>
        </div>
        <div className="attack-chain-meta">
          <span className="chain-complexity">Complexity: {chain.complexity}</span>
          <span className="chain-likelihood">Likelihood: {(chain.likelihood * 100).toFixed(0)}%</span>
        </div>
      </div>

      <p className="attack-goal">{chain.attack_goal}</p>
      <p className="business-impact">{chain.business_impact}</p>

      <div className="attack-steps-preview">
        <strong>{chain.steps.length} Steps:</strong>
        {chain.steps.map((step, idx) => (
          <span key={idx} className="step-preview">
            {idx + 1}. {step.http_method} {step.endpoint}
          </span>
        ))}
      </div>
    </div>
  );

  const renderChainDetails = (chain) => (
    <div className="chain-details-modal">
      <div className="modal-overlay" onClick={() => setSelectedChain(null)} />
      <div className="modal-content">
        <div className="modal-header">
          <h2>{chain.name}</h2>
          <button onClick={() => setSelectedChain(null)} className="close-btn">×</button>
        </div>

        <div className="modal-body">
          <div className="chain-overview">
            <div className="overview-item">
              <label>Attack Goal:</label>
              <p>{chain.attack_goal}</p>
            </div>
            <div className="overview-item">
              <label>Business Impact:</label>
              <p>{chain.business_impact}</p>
            </div>
            <div className="overview-item">
              <label>Attacker Profile:</label>
              <p>{chain.attacker_profile}</p>
            </div>
            <div className="overview-metrics">
              <div className="metric">
                <span className={`severity-badge severity-${chain.severity.toLowerCase()}`}>
                  {chain.severity}
                </span>
              </div>
              <div className="metric">
                <label>Complexity:</label>
                <span>{chain.complexity}</span>
              </div>
              <div className="metric">
                <label>Likelihood:</label>
                <span>{(chain.likelihood * 100).toFixed(0)}%</span>
              </div>
              <div className="metric">
                <label>Impact:</label>
                <span>{chain.impact_score.toFixed(1)}/10</span>
              </div>
            </div>
          </div>

          <div className="attack-steps-detailed">
            <h3>Attack Steps</h3>
            {chain.steps.map((step, idx) => (
              <div key={idx} className="attack-step">
                <div className="step-number">{step.step_number}</div>
                <div className="step-content">
                  <div className="step-header">
                    <span className="step-type">{step.step_type.replace('_', ' ').toUpperCase()}</span>
                    <span className="step-endpoint">
                      <code>{step.http_method} {step.endpoint}</code>
                    </span>
                  </div>
                  <p className="step-description"><strong>What attacker does:</strong> {step.description}</p>
                  <p className="step-technical"><strong>How to exploit:</strong> {step.technical_detail}</p>

                  {step.information_gained && step.information_gained.length > 0 && (
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
            ))}
          </div>

          <div className="remediation-section">
            <h3>How to Fix</h3>
            <div className="remediation-priority">
              Priority: <strong>{chain.remediation_priority}</strong>
            </div>
            <ol className="remediation-steps">
              {chain.remediation_steps.map((step, idx) => (
                <li key={idx}>{step}</li>
              ))}
            </ol>
          </div>
        </div>
      </div>
    </div>
  );

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
                color: riskInfo.color
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
        <button onClick={onClose} className="close-report-btn">Close Report</button>
      </div>

      <div className="report-tabs">
        <button
          className={activeTab === 'overview' ? 'active' : ''}
          onClick={() => setActiveTab('overview')}
        >
          Overview
        </button>
        <button
          className={activeTab === 'chains' ? 'active' : ''}
          onClick={() => setActiveTab('chains')}
        >
          Attack Chains ({total_chains_found})
        </button>
        <button
          className={activeTab === 'remediation' ? 'active' : ''}
          onClick={() => setActiveTab('remediation')}
        >
          Remediation
        </button>
      </div>

      <div className="report-content">
        {activeTab === 'overview' && (
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

        {activeTab === 'chains' && (
          <div className="chains-tab">
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
                <p>No attack chains discovered. Individual vulnerabilities may exist but cannot be easily chained together.</p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'remediation' && (
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

      {selectedChain && renderChainDetails(selectedChain)}
    </div>
  );
};

export default AttackPathReport;
