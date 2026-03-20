import React from "react";
import "./ContractSyncPanel.css";

const ContractSyncPanel = ({ verification, auth }) => {
  if (!verification && !auth) return null;

  const getSeverityClass = (severity) => {
    switch (severity?.toUpperCase()) {
      case "CRITICAL":
      case "ERROR":
        return "severity-error";
      case "HIGH":
      case "WARNING":
        return "severity-warning";
      case "MEDIUM":
      case "INFO":
        return "severity-info";
      default:
        return "severity-none";
    }
  };

  return (
    <div className="contract-sync-panel">
      <div className="sync-section">
        <div className="section-header">
          <h4>📋 Contract Alignment</h4>
          <span
            className={`sync-status ${verification?.is_synchronized ? "status-ok" : "status-fail"}`}
          >
            {verification?.is_synchronized
              ? "✅ Synchronized"
              : "❌ Out of Sync"}
          </span>
        </div>

        {verification?.issues && verification.issues.length > 0 ? (
          <ul className="issue-list">
            {verification.issues.map((issue, idx) => (
              <li
                key={idx}
                className={`issue-item ${getSeverityClass(issue.severity)}`}
              >
                <div className="issue-main">
                  <span className="issue-type">[{issue.type}]</span>
                  <span className="issue-desc">{issue.description}</span>
                </div>
                {(issue.spec_value || issue.code_value) && (
                  <div className="issue-diff">
                    {issue.spec_value && (
                      <div className="diff-spec">
                        Spec: <code>{issue.spec_value}</code>
                      </div>
                    )}
                    {issue.code_value && (
                      <div className="diff-code">
                        Code: <code>{issue.code_value}</code>
                      </div>
                    )}
                  </div>
                )}
              </li>
            ))}
          </ul>
        ) : (
          <p className="no-issues">Contract matches implementation exactly.</p>
        )}
      </div>

      <div className="sync-section">
        <div className="section-header">
          <h4>🛡️ Security Alignment</h4>
          <span
            className={`sync-status ${auth?.auth_synchronized ? "status-ok" : "status-fail"}`}
          >
            {auth?.auth_synchronized ? "✅ Authenticated" : "⚠️ Misaligned"}
          </span>
        </div>

        {auth?.issues && auth.issues.length > 0 && (
          <ul className="issue-list">
            {auth.issues.map((issue, idx) => (
              <li
                key={idx}
                className={`issue-item ${getSeverityClass(issue.severity)}`}
              >
                <span className="issue-desc">{issue.description}</span>
              </li>
            ))}
          </ul>
        )}

        <div className="auth-comparison">
          <div className="auth-box">
            <span className="label">Spec Auth:</span>
            <code>{auth?.spec_auth || "None"}</code>
          </div>
          <div className="auth-box">
            <span className="label">Code Auth:</span>
            <code>{auth?.code_auth || "None"}</code>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ContractSyncPanel;
