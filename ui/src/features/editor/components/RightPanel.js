import { useSpecStore } from "../../../store/specStore";
import React from 'react';
import "swagger-ui-react/swagger-ui.css"; // Ensure this is imported for Swagger UI

// Import the content components for each tab
import ValidationPanel from './ValidationPanel';
import EnhancedSwaggerUI from './EnhancedSwaggerUI';
import AIPanel from '../../ai/components/AIPanel';
import RepositoryPanel from '../../repository/components/RepositoryPanel';

function RightPanel() {
    // Get activeTab and setActiveTab action from the store
    const { activeTab, setActiveTab } = useSpecStore();

    return (
        <div className="right-panel-container">
            <div className="panel-tabs">
                <button
                    onClick={() => setActiveTab('validation')}
                    className={activeTab === 'validation' ? 'active' : ''}
                >
                    Validation
                </button>
                <button
                    onClick={() => setActiveTab('api_explorer')}
                    className={activeTab === 'api_explorer' ? 'active' : ''}
                >
                    API Explorer
                </button>
                <button
                    onClick={() => setActiveTab('ai_features')}
                    className={activeTab === 'ai_features' ? 'active' : ''}
                >
                    AI Features
                </button>
                <button
                    onClick={() => setActiveTab('repository')}
                    className={activeTab === 'repository' ? 'active' : ''}
                >
                    Repository
                </button>
            </div>
            <div className="panel-content">
                {activeTab === 'validation' && <ValidationPanel />}
                {activeTab === 'api_explorer' && <EnhancedSwaggerUI />}
                {activeTab === 'ai_features' && <AIPanel />}
                {activeTab === 'repository' && <RepositoryPanel />}
            </div>
        </div>
    );
}

export default RightPanel;