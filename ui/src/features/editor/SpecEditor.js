import React, { useEffect } from 'react';
import { Panel, PanelGroup, PanelResizeHandle } from "react-resizable-panels";
import { useSpecStore } from '../../store/specStore'; // Connect to our store

import EditorPanel from './components/EditorPanel';
import RightPanel from './components/RightPanel';
import './editor.css';

function SpecEditor() {
    // We only pull top-level actions needed for initial setup from the store
    const createSession = useSpecStore((state) => state.createSession);
    // Assuming websocketService.connect is called somewhere else or in createSession

    useEffect(() => {
        // Create a session when the component mounts
        createSession();
    }, [createSession]);

    return (
        <div className="spec-editor-layout">
            <PanelGroup direction="horizontal">
                <Panel defaultSize={60} minSize={30}>
                    <EditorPanel /> {/* This component will connect to the store internally */}
                </Panel>
                <PanelResizeHandle className="resize-handle" />
                <Panel defaultSize={40} minSize={20}>
                    <RightPanel /> {/* This component will connect to the store internally */}
                </Panel>
            </PanelGroup>
        </div>
    );
}

export default SpecEditor;