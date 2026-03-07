import React from "react";
import "./SecurityScoreCard.css";

const SecurityScoreCard = ({
  score,
  riskLevel,
  criticalCount,
  highCount,
  mediumCount,
  lowCount,
}) => {
  const getScoreColor = (score) => {
    if (score >= 80) return "var(--status-low)";
    if (score >= 60) return "var(--status-medium)";
    if (score >= 40) return "var(--status-high)";
    return "var(--status-critical)";
  };

  const getRiskBadgeClass = (level) => {
    const levelLower = (level || "medium").toLowerCase();
    return `badge badge-${levelLower === "critical" ? "critical" : levelLower === "high" ? "high" : levelLower === "low" ? "low" : "medium"}`;
  };

  return (
    <div className="security-score-card">
      <div className="score-header">
        <h3>Security Posture</h3>
      </div>

      <div className="score-main">
        <div
          className="score-circle"
          style={{ borderColor: getScoreColor(score) }}
        >
          <span className="score-value" style={{ color: getScoreColor(score) }}>
            {score || 0}
          </span>
          <span className="score-max">/100</span>
        </div>

        <div className="score-meta">
          <span className={getRiskBadgeClass(riskLevel)}>
            {(riskLevel || "UNKNOWN").toUpperCase()} RISK
          </span>
        </div>
      </div>

      <div className="severity-breakdown">
        <div className="severity-item severity-critical">
          <span className="severity-count">{criticalCount || 0}</span>
          <span className="severity-label">Critical</span>
        </div>
        <div className="severity-item severity-high">
          <span className="severity-count">{highCount || 0}</span>
          <span className="severity-label">High</span>
        </div>
        <div className="severity-item severity-medium">
          <span className="severity-count">{mediumCount || 0}</span>
          <span className="severity-label">Medium</span>
        </div>
        <div className="severity-item severity-low">
          <span className="severity-count">{lowCount || 0}</span>
          <span className="severity-label">Low</span>
        </div>
      </div>
    </div>
  );
};

export default SecurityScoreCard;
