import { useSpecStore } from "../../../store/specStore";
import React from "react";
import "swagger-ui-react/swagger-ui.css";

import ValidationPanel from "./ValidationPanel";
import EnhancedSwaggerUI from "./EnhancedSwaggerUI";
import AIPanel from "../../ai/components/AIPanel";
import RepositoryPanel from "../../repository/components/RepositoryPanel";
import ImplementationPanel from "./ImplementationPanel";

const TABS = [
  { id: "validation", label: "Validation", icon: "✓" },
  { id: "api_explorer", label: "API Explorer", icon: "🔍" },
  { id: "ai_features", label: "AI Features", icon: "🤖" },
  { id: "repository", label: "Repository", icon: "📁" },
  { id: "implementation", label: "Implementation", icon: "⚡" },
];

function RightPanel() {
  const {
    activeRightPanelTab,
    setActiveRightPanelTab,
    errors,
    suggestions,
    implementation,
  } = useSpecStore();

  const getTabBadge = (tabId) => {
    if (tabId === "validation") {
      const errorCount = errors?.length || 0;
      const sugCount = suggestions?.length || 0;
      const total = errorCount + sugCount;
      if (total > 0) {
        return (
          <span
            className={`tab-badge ${errorCount > 0 ? "badge-critical" : "badge-info"}`}
          >
            {total}
          </span>
        );
      }
    }
    if (tabId === "implementation" && implementation?.found) {
      return <span className="tab-badge badge-low">Linked</span>;
    }
    return null;
  };

  return (
    <div className="right-panel-wrapper">
      <div className="tab-list tab-list-underline">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveRightPanelTab(tab.id)}
            className={`tab-item ${activeRightPanelTab === tab.id ? "active" : ""}`}
          >
            <span className="tab-item-icon">{tab.icon}</span>
            <span>{tab.label}</span>
            {getTabBadge(tab.id)}
          </button>
        ))}
      </div>
      <div className="tab-content">
        {activeRightPanelTab === "validation" && <ValidationPanel />}
        {activeRightPanelTab === "api_explorer" && <EnhancedSwaggerUI />}
        {activeRightPanelTab === "ai_features" && <AIPanel />}
        {activeRightPanelTab === "repository" && <RepositoryPanel />}
        {activeRightPanelTab === "implementation" && <ImplementationPanel />}
      </div>
    </div>
  );
}

export default RightPanel;
