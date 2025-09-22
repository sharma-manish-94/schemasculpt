import { useSpecStore } from "../../../store/specStore";
import React from "react";
import { Panel, PanelGroup, PanelResizeHandle } from "react-resizable-panels";
import NavigationPanel from "./NavigationPanel";
import DetailPanel from "./DetailPanel";
import RightPanel from "./RightPanel";

function ThreePanelLayout() {
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
          <DetailPanel />
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
