import React from "react";
import { useSpecStore } from "../../../store/specStore";
import EditorPanel from "./EditorPanel";
import OperationSpecViewer from "./OperationSpecViewer";

function DetailPanel() {
    const { selectedNavItem, isNavItemLoading } = useSpecStore();

    if(isNavItemLoading) {
        return <div className="panel-content-placeholder"> Loading Details...</div>
    }

    return (
      <div className="detail-panel-wrapper">
      {!selectedNavItem ? (
        <EditorPanel />
      ) : (
        <OperationSpecViewer />
      )}
    </div>
  );
}

export default DetailPanel;
