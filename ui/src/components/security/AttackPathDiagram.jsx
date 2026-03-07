import React from "react";
import "./AttackPathDiagram.css";

const AttackPathDiagram = ({ steps, onStepClick }) => {
  if (!steps || steps.length === 0) {
    return (
      <div className="attack-path-empty">
        <p>No attack path steps available</p>
      </div>
    );
  }

  const getSeverityClass = (severity) => {
    const sev = (severity || "medium").toLowerCase();
    if (sev === "critical") return "severity-critical";
    if (sev === "high") return "severity-high";
    if (sev === "low") return "severity-low";
    return "severity-medium";
  };

  return (
    <div className="attack-path-diagram">
      <div className="path-flow">
        {steps.map((step, index) => (
          <React.Fragment key={index}>
            <div
              className={`path-node ${getSeverityClass(step.severity)}`}
              onClick={() => onStepClick && onStepClick(step, index)}
            >
              <div className="node-header">
                <span className="node-method">
                  {step.http_method || step.method || "API"}
                </span>
                <span className="node-endpoint">
                  {step.endpoint || step.path || "/"}
                </span>
              </div>
              <div className="node-vulnerability">
                {step.vulnerability_type || step.type || "Vulnerability"}
              </div>
              <span
                className={`badge badge-${(step.severity || "medium").toLowerCase()}`}
              >
                {(step.severity || "Medium").charAt(0).toUpperCase() +
                  (step.severity || "medium").slice(1)}
              </span>
            </div>
            {index < steps.length - 1 && (
              <div className="path-connector">
                <div className="connector-line"></div>
                <div className="connector-arrow">→</div>
              </div>
            )}
          </React.Fragment>
        ))}
      </div>
    </div>
  );
};

export default AttackPathDiagram;
