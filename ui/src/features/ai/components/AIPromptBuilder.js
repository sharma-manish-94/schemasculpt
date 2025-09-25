import React, { useState, useEffect } from 'react';
import { useSpecStore } from '../../../store/specStore';
import Button from '../../../components/ui/Button';
import LoadingSpinner from '../../../components/ui/LoadingSpinner';
import ErrorMessage from '../../../components/ui/ErrorMessage';

function AIPromptBuilder() {
    const {
        fetchAvailableTemplates,
        usePromptTemplate: applyPromptTemplate,
        generateIntelligentPrompt,
        optimizePrompt,
        fetchPromptStatistics,
        availableTemplates,
        promptStatistics,
        isAiProcessing
    } = useSpecStore();

    const [activeTab, setActiveTab] = useState('builder');
    const [currentPrompt, setCurrentPrompt] = useState('');
    const [optimizedPrompt, setOptimizedPrompt] = useState('');
    const [selectedTemplate, setSelectedTemplate] = useState('');
    const [templateVariables, setTemplateVariables] = useState({});
    const [generatedPrompt, setGeneratedPrompt] = useState('');
    const [contextId, setContextId] = useState('');
    const [requestData, setRequestData] = useState({
        operation_type: 'modify',
        context: 'openapi_specification',
        goal: 'improvement'
    });

    useEffect(() => {
        fetchAvailableTemplates();
        fetchPromptStatistics();
    }, [fetchAvailableTemplates, fetchPromptStatistics]);

    const handleTemplateSelect = (templateName) => {
        setSelectedTemplate(templateName);
        const template = availableTemplates?.templates?.[templateName];
        if (template?.variables) {
            const initialVariables = {};
            template.variables.forEach(variable => {
                initialVariables[variable] = '';
            });
            setTemplateVariables(initialVariables);
        }
    };

    const handleUseTemplate = async () => {
        if (!selectedTemplate) return;

        const result = await applyPromptTemplate(selectedTemplate, templateVariables);
        if (result.success && result.data) {
            setGeneratedPrompt(result.data.generated_prompt || '');
        }
    };

    const handleGenerateIntelligent = async () => {
        const result = await generateIntelligentPrompt(requestData, contextId || null);
        if (result.success && result.data) {
            setGeneratedPrompt(result.data.user_prompt || '');
        }
    };

    const handleOptimizePrompt = async () => {
        if (!currentPrompt.trim()) return;

        const result = await optimizePrompt({
            prompt: currentPrompt,
            operation_type: requestData.operation_type,
            goal: requestData.goal
        });

        if (result.success && result.data) {
            setOptimizedPrompt(result.data.optimized_prompt || '');
        }
    };

    const renderPromptBuilder = () => (
        <div className="prompt-builder">
            <div className="builder-section">
                <h5>Intelligent Prompt Generation</h5>
                <div className="form-group">
                    <label>Operation Type</label>
                    <select
                        value={requestData.operation_type}
                        onChange={(e) => setRequestData(prev => ({
                            ...prev,
                            operation_type: e.target.value
                        }))}
                    >
                        <option value="modify">Modify Specification</option>
                        <option value="enhance">Enhance Specification</option>
                        <option value="validate">Validate Specification</option>
                        <option value="generate">Generate New Content</option>
                        <option value="document">Add Documentation</option>
                        <option value="optimize">Optimize Structure</option>
                    </select>
                </div>

                <div className="form-group">
                    <label>Goal</label>
                    <select
                        value={requestData.goal}
                        onChange={(e) => setRequestData(prev => ({
                            ...prev,
                            goal: e.target.value
                        }))}
                    >
                        <option value="improvement">General Improvement</option>
                        <option value="clarity">Improve Clarity</option>
                        <option value="completeness">Add Completeness</option>
                        <option value="best_practices">Apply Best Practices</option>
                        <option value="performance">Optimize Performance</option>
                        <option value="security">Enhance Security</option>
                    </select>
                </div>

                <div className="form-group">
                    <label>Context ID (optional)</label>
                    <input
                        type="text"
                        placeholder="Context identifier for related operations"
                        value={contextId}
                        onChange={(e) => setContextId(e.target.value)}
                    />
                </div>

                <Button
                    variant="ai"
                    onClick={handleGenerateIntelligent}
                    loading={isAiProcessing}
                >
                    Generate Intelligent Prompt
                </Button>
            </div>

            {generatedPrompt && (
                <div className="generated-prompt-section">
                    <h5>Generated Prompt</h5>
                    <textarea
                        className="generated-prompt"
                        value={generatedPrompt}
                        onChange={(e) => setGeneratedPrompt(e.target.value)}
                        rows={6}
                    />
                    <div className="prompt-actions">
                        <Button
                            variant="primary"
                            size="small"
                            onClick={() => {
                                const { setAiPrompt } = useSpecStore.getState();
                                setAiPrompt(generatedPrompt);
                            }}
                        >
                            Use This Prompt
                        </Button>
                        <Button
                            variant="secondary"
                            size="small"
                            onClick={() => navigator.clipboard.writeText(generatedPrompt)}
                        >
                            Copy
                        </Button>
                    </div>
                </div>
            )}
        </div>
    );

    const renderTemplates = () => (
        <div className="prompt-templates">
            <div className="templates-section">
                <h5>Available Templates</h5>
                {!availableTemplates?.templates ? (
                    <LoadingSpinner />
                ) : (
                    <div className="template-list">
                        {Object.entries(availableTemplates.templates).map(([templateName, template]) => (
                            <div
                                key={templateName}
                                className={`template-item ${selectedTemplate === templateName ? 'selected' : ''}`}
                                onClick={() => handleTemplateSelect(templateName)}
                            >
                                <div className="template-info">
                                    <h6>{template.name}</h6>
                                    <p>{template.description}</p>
                                    <div className="template-variables">
                                        Variables: {template.variables?.join(', ') || 'None'}
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {selectedTemplate && (
                <div className="template-variables-section">
                    <h5>Template Variables</h5>
                    {Object.keys(templateVariables).map(variable => (
                        <div key={variable} className="form-group">
                            <label>{variable}</label>
                            <input
                                type="text"
                                value={templateVariables[variable]}
                                onChange={(e) => setTemplateVariables(prev => ({
                                    ...prev,
                                    [variable]: e.target.value
                                }))}
                                placeholder={`Enter value for ${variable}`}
                            />
                        </div>
                    ))}
                    <Button
                        variant="ai"
                        onClick={handleUseTemplate}
                        loading={isAiProcessing}
                    >
                        Apply Template
                    </Button>
                </div>
            )}
        </div>
    );

    const renderOptimizer = () => (
        <div className="prompt-optimizer">
            <div className="optimizer-section">
                <h5>Prompt Optimizer</h5>
                <div className="form-group">
                    <label>Current Prompt</label>
                    <textarea
                        placeholder="Enter your prompt to optimize..."
                        value={currentPrompt}
                        onChange={(e) => setCurrentPrompt(e.target.value)}
                        rows={6}
                    />
                </div>

                <Button
                    variant="ai"
                    onClick={handleOptimizePrompt}
                    disabled={!currentPrompt.trim()}
                    loading={isAiProcessing}
                >
                    Optimize Prompt
                </Button>
            </div>

            {optimizedPrompt && (
                <div className="optimized-prompt-section">
                    <h5>Optimized Prompt</h5>
                    <textarea
                        className="optimized-prompt"
                        value={optimizedPrompt}
                        onChange={(e) => setOptimizedPrompt(e.target.value)}
                        rows={6}
                    />
                    <div className="optimization-comparison">
                        <div className="comparison-metrics">
                            <div className="metric">
                                <span>Original Length:</span>
                                <span>{currentPrompt.length} chars</span>
                            </div>
                            <div className="metric">
                                <span>Optimized Length:</span>
                                <span>{optimizedPrompt.length} chars</span>
                            </div>
                            <div className="metric">
                                <span>Change:</span>
                                <span className={optimizedPrompt.length > currentPrompt.length ? 'positive' : 'negative'}>
                                    {optimizedPrompt.length - currentPrompt.length > 0 ? '+' : ''}
                                    {optimizedPrompt.length - currentPrompt.length} chars
                                </span>
                            </div>
                        </div>
                    </div>
                    <div className="prompt-actions">
                        <Button
                            variant="primary"
                            size="small"
                            onClick={() => {
                                const { setAiPrompt } = useSpecStore.getState();
                                setAiPrompt(optimizedPrompt);
                            }}
                        >
                            Use Optimized
                        </Button>
                        <Button
                            variant="secondary"
                            size="small"
                            onClick={() => setCurrentPrompt(optimizedPrompt)}
                        >
                            Replace Original
                        </Button>
                    </div>
                </div>
            )}
        </div>
    );

    const renderStatistics = () => (
        <div className="prompt-statistics">
            <h5>Prompt Statistics</h5>
            {!promptStatistics ? (
                <LoadingSpinner />
            ) : (
                <div className="stats-grid">
                    <div className="stat-card">
                        <div className="stat-label">Total Prompts Generated</div>
                        <div className="stat-value">{promptStatistics.total_prompts_generated || 0}</div>
                    </div>
                    <div className="stat-card">
                        <div className="stat-label">Average Prompt Length</div>
                        <div className="stat-value">{promptStatistics.average_prompt_length || 0} chars</div>
                    </div>
                    <div className="stat-card">
                        <div className="stat-label">Most Used Templates</div>
                        <div className="stat-value">
                            {promptStatistics.most_used_templates || 'None'}
                        </div>
                    </div>
                    {promptStatistics.status && (
                        <div className="stat-card">
                            <div className="stat-label">Service Status</div>
                            <div className="stat-value">{promptStatistics.status}</div>
                        </div>
                    )}
                </div>
            )}
        </div>
    );

    return (
        <div className="ai-prompt-builder">
            <div className="prompt-builder-header">
                <h4>AI Prompt Builder</h4>
                <div className="prompt-tabs">
                    <button
                        className={`prompt-tab ${activeTab === 'builder' ? 'active' : ''}`}
                        onClick={() => setActiveTab('builder')}
                    >
                        Builder
                    </button>
                    <button
                        className={`prompt-tab ${activeTab === 'templates' ? 'active' : ''}`}
                        onClick={() => setActiveTab('templates')}
                    >
                        Templates
                    </button>
                    <button
                        className={`prompt-tab ${activeTab === 'optimizer' ? 'active' : ''}`}
                        onClick={() => setActiveTab('optimizer')}
                    >
                        Optimizer
                    </button>
                    <button
                        className={`prompt-tab ${activeTab === 'stats' ? 'active' : ''}`}
                        onClick={() => setActiveTab('stats')}
                    >
                        Statistics
                    </button>
                </div>
            </div>

            <div className="prompt-builder-content">
                {activeTab === 'builder' && renderPromptBuilder()}
                {activeTab === 'templates' && renderTemplates()}
                {activeTab === 'optimizer' && renderOptimizer()}
                {activeTab === 'stats' && renderStatistics()}
            </div>
        </div>
    );
}

export default AIPromptBuilder;