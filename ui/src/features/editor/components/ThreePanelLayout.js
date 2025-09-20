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
        <DetailPanel />
      </Panel>
      <PanelResizeHandle className="resize-handle" />

      {/* Column 3 */}
      <Panel defaultSize={35} minSize={20} className="panel-container">
        <RightPanel />
      </Panel>
    </PanelGroup>
  );
}

export default ThreePanelLayout;
