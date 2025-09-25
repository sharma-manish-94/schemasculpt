import React, { useState, useEffect } from 'react';
import { useSpecStore } from '../../../store/specStore';
import Button from '../../../components/ui/Button';
import LoadingSpinner from '../../../components/ui/LoadingSpinner';
import ErrorMessage from '../../../components/ui/ErrorMessage';
import AIHealthStatus from './AIHealthStatus';
import AIAgentManager from './AIAgentManager';
import AIPromptBuilder from './AIPromptBuilder';
import AIWorkflowRunner from './AIWorkflowRunner';
import AISpecGenerator from './AISpecGenerator';
import '../ai-features.css';

const AI_TABS = {
    ASSISTANT: 'assistant',
    GENERATOR: 'generator',
    AGENTS: 'agents',
    WORKFLOWS: 'workflows',
    PROMPTS: 'prompts',
    HEALTH: 'health'
};

function AIPanel() {
    const [activeTab, setActiveTab] = useState(AI_TABS.ASSISTANT);
    const {
        aiPrompt,
        setAiPrompt,
        submitAIRequest,
        isAiProcessing,
        aiResponse,
        aiError,
        clearAiResponse,
        processSpecification,
        generateSpecification,
        checkAiHealth,
        aiHealthStatus,
        fetchAgentsStatus,
        agentsStatus
    } = useSpecStore();

    useEffect(() => {
        checkAiHealth();
        fetchAgentsStatus();
    }, [checkAiHealth, fetchAgentsStatus]);

    const handleQuickAction = async (actionType, prompt) => {
        clearAiResponse();

        const request = {
            operationType: actionType,
            prompt: prompt,
            streaming: false
        };

        await processSpecification(request);
    };

    const renderTabContent = () => {
        switch (activeTab) {
            case AI_TABS.ASSISTANT:
                return <AIAssistantTab />;
            case AI_TABS.GENERATOR:
                return <AISpecGenerator />;
            case AI_TABS.AGENTS:
                return <AIAgentManager />;
            case AI_TABS.WORKFLOWS:
                return <AIWorkflowRunner />;
            case AI_TABS.PROMPTS:
                return <AIPromptBuilder />;
            case AI_TABS.HEALTH:
                return <AIHealthStatus />;
            default:
                return <AIAssistantTab />;
        }
    };

    return (
        <div className="ai-panel">
            <div className="ai-panel-header">
                <h3>AI Features</h3>
                <div className="ai-tabs">
                    {Object.entries(AI_TABS).map(([key, value]) => (
                        <button
                            key={value}
                            className={`ai-tab ${activeTab === value ? 'active' : ''}`}
                            onClick={() => setActiveTab(value)}
                        >
                            {key.charAt(0) + key.slice(1).toLowerCase()}
                        </button>
                    ))}
                </div>
            </div>

            <div className="ai-panel-content">
                {renderTabContent()}
            </div>

            {/* Quick Actions Bar */}
            <div className="ai-quick-actions">
                <h4>Quick Actions</h4>
                <div className="quick-action-buttons">
                    <Button
                        variant="ai"
                        size="small"
                        onClick={() => handleQuickAction('ENHANCE', 'Improve this API specification with better descriptions and examples')}
                        loading={isAiProcessing}
                    >
                        Enhance
                    </Button>
                    <Button
                        variant="ai"
                        size="small"
                        onClick={() => handleQuickAction('VALIDATE', 'Validate this API specification and suggest improvements')}
                        loading={isAiProcessing}
                    >
                        Validate
                    </Button>
                    <Button
                        variant="ai"
                        size="small"
                        onClick={() => handleQuickAction('DOCUMENT', 'Add comprehensive documentation to this API specification')}
                        loading={isAiProcessing}
                    >
                        Document
                    </Button>
                    <Button
                        variant="ai"
                        size="small"
                        onClick={() => handleQuickAction('OPTIMIZE', 'Optimize this API specification for better performance and usability')}
                        loading={isAiProcessing}
                    >
                        Optimize
                    </Button>
                </div>
            </div>

            {/* Response/Error Display */}
            {aiError && (
                <div className="ai-response-section">
                    <ErrorMessage message={aiError} />
                </div>
            )}

            {aiResponse && (
                <div className="ai-response-section">
                    <h4>AI Response</h4>
                    <div className="ai-response-content">
                        <pre>{JSON.stringify(aiResponse, null, 2)}</pre>
                    </div>
                    <Button
                        variant="secondary"
                        size="small"
                        onClick={clearAiResponse}
                    >
                        Clear Response
                    </Button>
                </div>
            )}
        </div>
    );
}

function AIAssistantTab() {
    const {
        aiPrompt,
        setAiPrompt,
        submitAIRequest,
        processSpecification,
        isAiProcessing,
        isStreaming
    } = useSpecStore();

    const [streamingMode, setStreamingMode] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!aiPrompt.trim()) return;

        if (streamingMode) {
            const request = {
                operationType: 'MODIFY',
                prompt: aiPrompt,
                streaming: 'REALTIME'
            };
            await processSpecification(request);
        } else {
            await submitAIRequest();
        }
    };

    return (
        <div className="ai-assistant-tab">
            <div className="ai-settings">
                <label>
                    <input
                        type="checkbox"
                        checked={streamingMode}
                        onChange={(e) => setStreamingMode(e.target.checked)}
                    />
                    Enable Streaming Mode
                </label>
            </div>

            <form className="ai-assistant-form" onSubmit={handleSubmit}>
                <div className="ai-input-group">
                    <textarea
                        className="ai-input"
                        placeholder="Describe what you want to do with your API specification..."
                        value={aiPrompt}
                        onChange={(e) => setAiPrompt(e.target.value)}
                        disabled={isAiProcessing}
                        rows={4}
                    />
                    <div className="ai-input-actions">
                        <Button
                            type="submit"
                            variant="ai"
                            loading={isAiProcessing}
                            disabled={!aiPrompt.trim()}
                        >
                            {streamingMode ? 'Stream Process' : 'Process'}
                        </Button>
                    </div>
                </div>
            </form>

            {isStreaming && (
                <div className="streaming-indicator">
                    <LoadingSpinner />
                    <span>Streaming response...</span>
                </div>
            )}

            <div className="ai-suggestions">
                <h4>Suggestion Templates</h4>
                <div className="suggestion-buttons">
                    <Button
                        variant="secondary"
                        size="small"
                        onClick={() => setAiPrompt('Add input validation to all POST endpoints')}
                    >
                        Add Validation
                    </Button>
                    <Button
                        variant="secondary"
                        size="small"
                        onClick={() => setAiPrompt('Add error response schemas to all endpoints')}
                    >
                        Add Error Schemas
                    </Button>
                    <Button
                        variant="secondary"
                        size="small"
                        onClick={() => setAiPrompt('Add authentication security scheme')}
                    >
                        Add Security
                    </Button>
                    <Button
                        variant="secondary"
                        size="small"
                        onClick={() => setAiPrompt('Generate realistic example responses')}
                    >
                        Add Examples
                    </Button>
                </div>
            </div>
        </div>
    );
}

export default AIPanel;