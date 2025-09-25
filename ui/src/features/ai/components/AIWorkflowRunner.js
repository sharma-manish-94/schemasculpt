import React, { useState, useEffect } from 'react';
import { useSpecStore } from '../../../store/specStore';
import Button from '../../../components/ui/Button';
import LoadingSpinner from '../../../components/ui/LoadingSpinner';
import ErrorMessage from '../../../components/ui/ErrorMessage';

function AIWorkflowRunner() {
    const {
        executeWorkflow,
        executeCustomWorkflow,
        fetchAvailableWorkflows,
        availableWorkflows,
        isAiProcessing,
        aiResponse,
        aiError
    } = useSpecStore();

    const [selectedWorkflow, setSelectedWorkflow] = useState('');
    const [workflowInputs, setWorkflowInputs] = useState({});
    const [customWorkflow, setCustomWorkflow] = useState({
        workflow_type: 'custom',
        steps: [],
        name: '',
        description: ''
    });
    const [workflowResults, setWorkflowResults] = useState([]);
    const [activeTab, setActiveTab] = useState('predefined');

    useEffect(() => {
        fetchAvailableWorkflows();
    }, [fetchAvailableWorkflows]);

    const handleWorkflowSelect = (workflowName) => {
        setSelectedWorkflow(workflowName);
        setWorkflowInputs({});
    };

    const handleExecuteWorkflow = async () => {
        if (!selectedWorkflow) return;

        const result = await executeWorkflow(selectedWorkflow, workflowInputs);

        if (result.success) {
            setWorkflowResults(prev => [
                {
                    id: Date.now(),
                    timestamp: new Date(),
                    workflowName: selectedWorkflow,
                    type: 'predefined',
                    result: result.data
                },
                ...prev
            ]);
        }
    };

    const handleExecuteCustomWorkflow = async () => {
        if (!customWorkflow.name || customWorkflow.steps.length === 0) return;

        const result = await executeCustomWorkflow(customWorkflow);

        if (result.success) {
            setWorkflowResults(prev => [
                {
                    id: Date.now(),
                    timestamp: new Date(),
                    workflowName: customWorkflow.name,
                    type: 'custom',
                    result: result.data
                },
                ...prev
            ]);
        }
    };

    const addCustomWorkflowStep = () => {
        setCustomWorkflow(prev => ({
            ...prev,
            steps: [
                ...prev.steps,
                {
                    id: Date.now(),
                    action: 'modify',
                    prompt: '',
                    options: {}
                }
            ]
        }));
    };

    const updateCustomWorkflowStep = (stepId, field, value) => {
        setCustomWorkflow(prev => ({
            ...prev,
            steps: prev.steps.map(step =>
                step.id === stepId ? { ...step, [field]: value } : step
            )
        }));
    };

    const removeCustomWorkflowStep = (stepId) => {
        setCustomWorkflow(prev => ({
            ...prev,
            steps: prev.steps.filter(step => step.id !== stepId)
        }));
    };

    const renderPredefinedWorkflows = () => (
        <div className="predefined-workflows">
            <div className="workflow-selection">
                <h5>Available Workflows</h5>
                {!availableWorkflows?.workflows ? (
                    <LoadingSpinner />
                ) : (
                    <div className="workflow-list">
                        {Object.entries(availableWorkflows.workflows).map(([workflowName, workflow]) => (
                            <div
                                key={workflowName}
                                className={`workflow-item ${selectedWorkflow === workflowName ? 'selected' : ''}`}
                                onClick={() => handleWorkflowSelect(workflowName)}
                            >
                                <div className="workflow-info">
                                    <h6>{workflow.name || workflowName}</h6>
                                    <p>{workflow.description || 'No description available'}</p>
                                    {workflow.inputs && (
                                        <div className="workflow-inputs-info">
                                            Required inputs: {workflow.inputs.join(', ')}
                                        </div>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {selectedWorkflow && (
                <div className="workflow-execution">
                    <h5>Workflow Inputs</h5>
                    <div className="workflow-inputs">
                        <div className="input-group">
                            <label>Specification Context</label>
                            <textarea
                                placeholder="Current OpenAPI specification context..."
                                value={workflowInputs.spec_context || ''}
                                onChange={(e) => setWorkflowInputs(prev => ({
                                    ...prev,
                                    spec_context: e.target.value
                                }))}
                                rows={4}
                            />
                        </div>

                        <div className="input-group">
                            <label>Additional Parameters</label>
                            <textarea
                                placeholder="Additional workflow parameters (JSON format)..."
                                value={workflowInputs.parameters || ''}
                                onChange={(e) => setWorkflowInputs(prev => ({
                                    ...prev,
                                    parameters: e.target.value
                                }))}
                                rows={3}
                            />
                        </div>

                        <div className="input-group">
                            <label>Target Goals</label>
                            <input
                                type="text"
                                placeholder="What do you want to achieve with this workflow?"
                                value={workflowInputs.goals || ''}
                                onChange={(e) => setWorkflowInputs(prev => ({
                                    ...prev,
                                    goals: e.target.value
                                }))}
                            />
                        </div>
                    </div>

                    <Button
                        variant="ai"
                        onClick={handleExecuteWorkflow}
                        loading={isAiProcessing}
                    >
                        Execute Workflow
                    </Button>
                </div>
            )}
        </div>
    );

    const renderCustomWorkflow = () => (
        <div className="custom-workflow">
            <div className="workflow-metadata">
                <h5>Custom Workflow</h5>
                <div className="metadata-inputs">
                    <div className="input-group">
                        <label>Workflow Name</label>
                        <input
                            type="text"
                            placeholder="My Custom Workflow"
                            value={customWorkflow.name}
                            onChange={(e) => setCustomWorkflow(prev => ({
                                ...prev,
                                name: e.target.value
                            }))}
                        />
                    </div>
                    <div className="input-group">
                        <label>Description</label>
                        <textarea
                            placeholder="Describe what this workflow does..."
                            value={customWorkflow.description}
                            onChange={(e) => setCustomWorkflow(prev => ({
                                ...prev,
                                description: e.target.value
                            }))}
                            rows={2}
                        />
                    </div>
                </div>
            </div>

            <div className="workflow-steps">
                <div className="steps-header">
                    <h5>Workflow Steps</h5>
                    <Button
                        variant="secondary"
                        size="small"
                        onClick={addCustomWorkflowStep}
                    >
                        Add Step
                    </Button>
                </div>

                {customWorkflow.steps.length === 0 ? (
                    <div className="no-steps">No steps defined. Click "Add Step" to begin.</div>
                ) : (
                    <div className="steps-list">
                        {customWorkflow.steps.map((step, index) => (
                            <div key={step.id} className="workflow-step">
                                <div className="step-header">
                                    <span className="step-number">Step {index + 1}</span>
                                    <Button
                                        variant="danger"
                                        size="small"
                                        onClick={() => removeCustomWorkflowStep(step.id)}
                                    >
                                        Remove
                                    </Button>
                                </div>
                                <div className="step-content">
                                    <div className="input-group">
                                        <label>Action</label>
                                        <select
                                            value={step.action}
                                            onChange={(e) => updateCustomWorkflowStep(step.id, 'action', e.target.value)}
                                        >
                                            <option value="modify">Modify</option>
                                            <option value="enhance">Enhance</option>
                                            <option value="validate">Validate</option>
                                            <option value="generate">Generate</option>
                                            <option value="document">Document</option>
                                            <option value="optimize">Optimize</option>
                                        </select>
                                    </div>
                                    <div className="input-group">
                                        <label>Prompt</label>
                                        <textarea
                                            placeholder="Describe what this step should do..."
                                            value={step.prompt}
                                            onChange={(e) => updateCustomWorkflowStep(step.id, 'prompt', e.target.value)}
                                            rows={3}
                                        />
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}

                {customWorkflow.steps.length > 0 && (
                    <div className="workflow-actions">
                        <Button
                            variant="ai"
                            onClick={handleExecuteCustomWorkflow}
                            loading={isAiProcessing}
                            disabled={!customWorkflow.name}
                        >
                            Execute Custom Workflow
                        </Button>
                    </div>
                )}
            </div>
        </div>
    );

    const renderWorkflowResults = () => (
        <div className="workflow-results">
            <h5>Workflow Results</h5>
            {workflowResults.length === 0 ? (
                <div className="no-results">No workflow results yet</div>
            ) : (
                <div className="results-list">
                    {workflowResults.map((result) => (
                        <div key={result.id} className="result-item">
                            <div className="result-header">
                                <div className="result-info">
                                    <h6>{result.workflowName}</h6>
                                    <span className={`result-type ${result.type}`}>
                                        {result.type}
                                    </span>
                                    <span className="result-timestamp">
                                        {result.timestamp.toLocaleString()}
                                    </span>
                                </div>
                                <div className="result-status">
                                    {result.result.status === 'success' ? '✓' : '✗'}
                                </div>
                            </div>
                            <div className="result-content">
                                <pre>{JSON.stringify(result.result, null, 2)}</pre>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );

    return (
        <div className="ai-workflow-runner">
            <div className="workflow-header">
                <h4>AI Workflow Runner</h4>
                <div className="workflow-tabs">
                    <button
                        className={`workflow-tab ${activeTab === 'predefined' ? 'active' : ''}`}
                        onClick={() => setActiveTab('predefined')}
                    >
                        Predefined
                    </button>
                    <button
                        className={`workflow-tab ${activeTab === 'custom' ? 'active' : ''}`}
                        onClick={() => setActiveTab('custom')}
                    >
                        Custom
                    </button>
                    <button
                        className={`workflow-tab ${activeTab === 'results' ? 'active' : ''}`}
                        onClick={() => setActiveTab('results')}
                    >
                        Results ({workflowResults.length})
                    </button>
                </div>
            </div>

            <div className="workflow-content">
                {activeTab === 'predefined' && renderPredefinedWorkflows()}
                {activeTab === 'custom' && renderCustomWorkflow()}
                {activeTab === 'results' && renderWorkflowResults()}
            </div>

            {aiError && (
                <div className="workflow-error">
                    <ErrorMessage message={aiError} />
                </div>
            )}

            {isAiProcessing && (
                <div className="workflow-processing">
                    <LoadingSpinner />
                    <span>Executing workflow...</span>
                </div>
            )}
        </div>
    );
}

export default AIWorkflowRunner;