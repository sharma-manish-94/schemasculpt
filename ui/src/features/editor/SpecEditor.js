import React, { useEffect } from "react";
import { useSpecStore } from "../../store/specStore";
import { useRequestStore } from "../../store/requestStore";
import ThreePanelLayout from "./components/ThreePanelLayout"; // Import our new layout
import "./editor.css";

function SpecEditor() {
  const createSession = useSpecStore((state) => state.createSession);
  const specText = useSpecStore((state) => state.specText);
  const parseEndpoints = useRequestStore((state) => state.parseEndpoints);

  useEffect(() => {
    createSession();
  }, [createSession]);

  // Parse endpoints whenever the spec text changes
  useEffect(() => {
    parseEndpoints();
  }, [specText, parseEndpoints]);

  //   return (
  //     <div className="app-container">
  //       <header className="App-header">{/* Your existing header JSX */}</header>
  //       <main className="App-main">
  //         <div className="spec-editor-wrapper">
  //           <ThreePanelLayout />
  //         </div>
  //       </main>
  //     </div>
  //   );
  return <ThreePanelLayout />;
}

export default SpecEditor;
