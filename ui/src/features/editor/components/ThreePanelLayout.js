import { useSpecStore } from "../../../store/specStore";
import { useAuth } from "../../../contexts/AuthContext";
import { projectAPI } from "../../../api/projectAPI";
import React, { useState } from "react";
import { Panel, PanelGroup, PanelResizeHandle } from "react-resizable-panels";
import NavigationPanel from "./NavigationPanel";
import DetailPanel from "./DetailPanel";
import RightPanel from "./RightPanel";

function ThreePanelLayout({ project }) {
  const specText = useSpecStore((state) => state.specText);
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    if (!project) {
      alert("No project selected");
      return;
    }

    const commitMessage = prompt("Enter a commit message for this version:");
    if (!commitMessage) {
      return; // User cancelled
    }

    setSaving(true);
    try {
      const specData = {
        specContent: specText,
        specFormat: "yaml",
        commitMessage,
      };

      await projectAPI.saveSpecification(project.id, specData);
      alert("Specification saved successfully!");
    } catch (error) {
      console.error("Failed to save specification:", error);
      alert(error.response?.data?.message || "Failed to save specification");
    } finally {
      setSaving(false);
    }
  };

  return (
    <PanelGroup direction="horizontal" className="main-layout">
      {/* Column 1 */}
      <Panel defaultSize={20} minSize={15} className="panel-container">
        <NavigationPanel />
      </Panel>
      <PanelResizeHandle className="resize-handle" />

      {/* Column 2 */}
      <Panel defaultSize={45} minSize={30} className="panel-container">
        <div className="panel-header">
          <span className="panel-icon">📝</span>
          Spec Editor
        </div>
        <div className="panel-content editor-panel-content">
          <DetailPanel project={project} />
        </div>
      </Panel>
      <PanelResizeHandle className="resize-handle" />

      {/* Column 3 */}
      <Panel defaultSize={35} minSize={20} className="panel-container">
        <div className="panel-header">
          <span className="panel-icon">🧪</span>
          API Explorer
        </div>
        <div className="panel-content">
          <RightPanel />
        </div>
      </Panel>
    </PanelGroup>
  );
}

export default ThreePanelLayout;
