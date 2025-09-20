import { useSpecStore } from "../../../store/specStore";
import React from 'react';
import SwaggerUI from 'swagger-ui-react';
import "swagger-ui-react/swagger-ui.css"; // Ensure this is imported for Swagger UI

// Import the content components for each tab
import ValidationPanel from './ValidationPanel';
import AILabPanel from './AILabPanel';
import InspectionPanel from './InspectionPanel';

function RightPanel() {
    // Get activeTab and setActiveTab action from the store
    const { specText, activeTab, setActiveTab } = useSpecStore();

    // Get selected operation from navigation
    const selectedNavItem = useSpecStore((state) => state.selectedNavItem);

    // Parse specText for SwaggerUI
    const parsedSpec = React.useMemo(() => {
        try {
            return JSON.parse(specText);
        } catch (error) {
            console.error('Failed to parse spec for SwaggerUI:', error);
            return null;
        }
    }, [specText]);

    // Determine what to show in the visualize tab based on selection
    const renderVisualizeContent = () => {
        if (!parsedSpec) {
            return (
                <div className="panel-content-placeholder">
                    Invalid JSON - cannot display visualization
                </div>
            );
        }

        // If an operation is selected, show detailed inspection
        if (selectedNavItem) {
            return <InspectionPanel />;
        }

        // If no operation selected, show full SwaggerUI
        return <SwaggerUI spec={parsedSpec} />;
    };

    return (
        <div className="right-panel-container">
            <div className="panel-tabs">
                <button onClick={() => setActiveTab('validation')} className={activeTab === 'validation' ? 'active' : ''}>Validation</button>
                <button onClick={() => setActiveTab('visualize')} className={activeTab === 'visualize' ? 'active' : ''}>
                    {selectedNavItem ? 'Inspect' : 'Visualize'}
                </button>
                <button onClick={() => setActiveTab('api_lab')} className={activeTab === 'api_lab' ? 'active' : ''}>API Lab</button>
            </div>
            <div className="panel-content">
                {activeTab === 'validation' && <ValidationPanel />}
                {activeTab === 'visualize' && renderVisualizeContent()}
                {activeTab === 'api_lab' && <AILabPanel />}
            </div>
        </div>
    );
}

export default RightPanel;