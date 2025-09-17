import React from "react";
import { useRequestStore } from "../../../store/requestStore";
import EditorPanel from "./EditorPanel";
import OperationEditorForm from "./OperationEditorForm";

function DetailPanel() {
  const selectedNavItem = useRequestStore((state) => state.selectedNavItem);

  return (
    <>
      {!selectedNavItem ? (
        <EditorPanel />
      ) : (
        <OperationEditorForm endpoint={selectedNavItem} />
      )}
    </>
  );
}

export default DetailPanel;
