import React from 'react';
import SwaggerUI from 'swagger-ui-react';
import "swagger-ui-react/swagger-ui.css"; // Ensure this is imported for Swagger UI
import { useSpecStore } from '../../../store/specStore'; // Connect to our store

// Import the content components for each tab
import ValidationPanel from './ValidationPanel';
import AILabPanel from './AILabPanel';

function RightPanel() {
    // Get activeTab and setActiveTab action from the store
    const { specText, activeTab, setActiveTab } = useSpecStore();

    return (
        <div className="right-panel-container">
            <div className="panel-tabs">
                <button onClick={() => setActiveTab('validation')} className={activeTab === 'validation' ? 'active' : ''}>Validation</button>
                <button onClick={() => setActiveTab('visualize')} className={activeTab === 'visualize' ? 'active' : ''}>Visualize</button>
                <button onClick={() => setActiveTab('api_lab')} className={activeTab === 'api_lab' ? 'active' : ''}>API Lab</button>
            </div>
            <div className="panel-content">
                {activeTab === 'validation' && <ValidationPanel />}
                {activeTab === 'visualize' && <SwaggerUI spec={specText} />}
                {activeTab === 'api_lab' && <AILabPanel />}
            </div>
        </div>
    );
}

export default RightPanel;