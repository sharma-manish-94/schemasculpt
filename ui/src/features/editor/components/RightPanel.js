import { useSpecStore } from "../../../store/specStore";
import React from "react";
import "swagger-ui-react/swagger-ui.css";

// Import the content components for each tab
import ValidationPanel from "./ValidationPanel";
import EnhancedSwaggerUI from "./EnhancedSwaggerUI";
import AIPanel from "../../ai/components/AIPanel";
import RepositoryPanel from "../../repository/components/RepositoryPanel";
import ImplementationPanel from "./ImplementationPanel";

function RightPanel() {
  const { activeRightPanelTab, setActiveRightPanelTab } = useSpecStore();

  return (
    <div className="right-panel-container">
      <div className="panel-tabs">
        <button
          onClick={() => setActiveRightPanelTab("validation")}
          className={activeRightPanelTab === "validation" ? "active" : ""}
        >
          Validation
        </button>
        <button
          onClick={() => setActiveRightPanelTab("api_explorer")}
          className={activeRightPanelTab === "api_explorer" ? "active" : ""}
        >
          API Explorer
        </button>
        <button
          onClick={() => setActiveRightPanelTab("ai_features")}
          className={activeRightPanelTab === "ai_features" ? "active" : ""}
        >
          AI Features
        </button>
        <button
          onClick={() => setActiveRightPanelTab("repository")}
          className={activeRightPanelTab === "repository" ? "active" : ""}
        >
          Repository
        </button>
        <button
          onClick={() => setActiveRightPanelTab("implementation")}
          className={activeRightPanelTab === "implementation" ? "active" : ""}
        >
          Implementation
        </button>
      </div>
      <div className="panel-content">
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
