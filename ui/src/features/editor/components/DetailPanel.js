import React from "react";
import { useSpecStore } from "../../../store/specStore";
import EnhancedEditorPanel from "./EnhancedEditorPanel";
import OperationSpecViewer from "./OperationSpecViewer";

function DetailPanel() {
    const { selectedNavItem, isNavItemLoading } = useSpecStore();

    if(isNavItemLoading) {
        return <div className="panel-content-placeholder"> Loading Details...</div>
    }

    return (
      <div className="detail-panel-wrapper">
      {!selectedNavItem ? (
        <EnhancedEditorPanel />
      ) : (
        <OperationSpecViewer />
      )}
    </div>
  );
}

export default DetailPanel;
