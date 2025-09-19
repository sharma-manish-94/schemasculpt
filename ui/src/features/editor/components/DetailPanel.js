import React from "react";
import { useRequestStore } from "../../../store/requestStore";
import EditorPanel from "./EditorPanel";
import OperationEditorForm from "./OperationEditorForm";

function DetailPanel() {
  const selectedNavItem = useRequestStore((state) => state.selectedNavItem);

  return (
      <div className="detail-panel-wrapper">
      {!selectedNavItem ? (
        <EditorPanel />
      ) : (
        <OperationEditorForm endpoint={selectedNavItem} />
      )}
    </div>
  );
}

export default DetailPanel;
