import React, { useEffect } from "react";
import { useSpecStore } from "../../store/specStore";
import { useRequestStore } from "../../store/requestStore";
import ThreePanelLayout from "./components/ThreePanelLayout"; // Import our new layout
import "./editor.css";

function SpecEditor() {
  const createSession = useSpecStore((state) => state.createSession);
  const connectWebSocket = useSpecStore((state) => state.connectWebSocket);
  const specText = useSpecStore((state) => state.specText);
  const parseEndpoints = useRequestStore((state) => state.parseEndpoints);

  useEffect(() => {
    const initializeSession = async () => {
      try {
        const sessionId = await createSession();
        if (sessionId) {
          connectWebSocket();
        }
      } catch (error) {
        console.error('Failed to initialize session:', error);
      }
    };

    initializeSession();
  }, [createSession, connectWebSocket]);

  // Parse endpoints whenever the spec text changes
  useEffect(() => {
    parseEndpoints();
  }, [specText, parseEndpoints]);

  return <ThreePanelLayout />;
}

export default SpecEditor;
