import React, { useEffect } from "react";
import { useSpecStore } from "../../store/specStore";
import ThreePanelLayout from "./components/ThreePanelLayout"; // Import our new layout
import "./editor.css";

function SpecEditor({ project }) {
  const createSession = useSpecStore((state) => state.createSession);
  const connectWebSocket = useSpecStore((state) => state.connectWebSocket);
  const specText = useSpecStore((state) => state.specText);
  const parseEndpoints = useSpecStore((state) => state.parseEndpoints);

  const setProjectId = useSpecStore((state) => state.setProjectId);

  useEffect(() => {
    if (project?.id) {
      setProjectId(project.id);
    }

    const initializeSession = async () => {
      try {
        const sessionId = await createSession();
        if (sessionId) {
          connectWebSocket();
        }
      } catch (error) {
        console.error("Failed to initialize session:", error);
      }
    };

    initializeSession();
  }, [project?.id, setProjectId, createSession, connectWebSocket]);

  // Parse endpoints whenever the spec text changes
  useEffect(() => {
    parseEndpoints();
  }, [specText, parseEndpoints]);

  return <ThreePanelLayout project={project} />;
}

export default SpecEditor;
