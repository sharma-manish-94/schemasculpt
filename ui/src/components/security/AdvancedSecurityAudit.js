/**
 * Advanced Security Audit Button Component
 *
 * Triggers the AI-powered attack path simulation and displays the results.
 * This is the entry point for the "Wow" feature.
 */

import React, { useState } from 'react';
import { runAttackPathSimulation } from '../../api/attackPathService';
import AttackPathReport from './AttackPathReport';
import './AdvancedSecurityAudit.css';

const AdvancedSecurityAudit = ({ sessionId }) => {
  const [isRunning, setIsRunning] = useState(false);
  const [report, setReport] = useState(null);
  const [error, setError] = useState(null);
  const [progress, setProgress] = useState(0);

  const handleRunAudit = async () => {
    setIsRunning(true);
    setError(null);
    setProgress(0);

    // Simulate progress (since we don't have WebSocket yet)
    const progressInterval = setInterval(() => {
      setProgress(prev => {
        if (prev >= 90) {
          clearInterval(progressInterval);
          return 90;
        }
        return prev + 10;
      });
    }, 1000);

    try {
      const result = await runAttackPathSimulation(sessionId, {
        analysisDepth: 'standard',
        maxChainLength: 5
      });

      clearInterval(progressInterval);
      setProgress(100);
      setReport(result);
    } catch (err) {
      clearInterval(progressInterval);
      setError(err.message || 'Failed to run attack path simulation');
      console.error('Attack path simulation error:', err);
    } finally {
      setIsRunning(false);
    }
  };

  const handleCloseReport = () => {
    setReport(null);
    setProgress(0);
  };

  if (report) {
    return <AttackPathReport report={report} onClose={handleCloseReport} />;
  }

  return (
    <div className="advanced-security-audit">
      <div className="audit-card">
        <div className="audit-header">
          <div className="audit-icon">🔒</div>
          <div className="audit-title">
            <h3>Advanced Security Audit</h3>
            <p>AI-Powered Attack Path Simulation</p>
          </div>
        </div>

        <div className="audit-description">
          <p>
            Discover multi-step attack chains that real hackers could exploit.
            Our AI agent thinks like an attacker to find vulnerabilities that
            can be chained together for high-impact exploits.
          </p>

          <div className="audit-features">
            <div className="feature">
              <span className="feature-icon">🔍</span>
              <span>Finds individual vulnerabilities</span>
            </div>
            <div className="feature">
              <span className="feature-icon">⛓️</span>
              <span>Discovers attack chains</span>
            </div>
            <div className="feature">
              <span className="feature-icon">📊</span>
              <span>Executive-level reports</span>
            </div>
            <div className="feature">
              <span className="feature-icon">🛡️</span>
              <span>Remediation roadmap</span>
            </div>
          </div>
        </div>

        {error && (
          <div className="audit-error">
            <strong>Error:</strong> {error}
          </div>
        )}

        {isRunning && (
          <div className="audit-progress">
            <div className="progress-label">
              Running attack path simulation... {progress}%
            </div>
            <div className="progress-bar">
              <div
                className="progress-fill"
                style={{ width: `${progress}%` }}
              />
            </div>
            <div className="progress-stages">
              <div className={progress >= 30 ? 'active' : ''}>
                🔍 Scanning vulnerabilities
              </div>
              <div className={progress >= 60 ? 'active' : ''}>
                🤖 AI analyzing attack chains
              </div>
              <div className={progress >= 90 ? 'active' : ''}>
                📝 Generating report
              </div>
            </div>
          </div>
        )}

        <button
          className="run-audit-btn"
          onClick={handleRunAudit}
          disabled={isRunning}
        >
          {isRunning ? 'Running Analysis...' : '🚀 Run Advanced Security Audit'}
        </button>

        <div className="audit-info">
          <small>
            ⚡ Powered by AI agents using LLM reasoning to simulate real-world attacks
          </small>
        </div>
      </div>
    </div>
  );
};

export default AdvancedSecurityAudit;
