import React, { useState, useEffect } from 'react';
import { useSpecStore } from '../../../store/specStore';
import Button from '../../../components/ui/Button';
import LoadingSpinner from '../../../components/ui/LoadingSpinner';
import ErrorMessage from '../../../components/ui/ErrorMessage';

function AIAgentManager() {
    const {
        fetchAgentsStatus,
        fetchSpecificAgentStatus,
        restartAgent,
        fetchAgentsPerformance,
        fetchAgentsCapabilities,
        agentsStatus,
        agentsPerformance,
        agentsCapabilities,
        isAiProcessing
    } = useSpecStore();

    const [selectedAgent, setSelectedAgent] = useState(null);
    const [agentDetails, setAgentDetails] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    useEffect(() => {
        const loadInitialData = async () => {
            await Promise.all([
                fetchAgentsStatus(),
                fetchAgentsPerformance(),
                fetchAgentsCapabilities()
            ]);
        };

        loadInitialData();
    }, [fetchAgentsStatus, fetchAgentsPerformance, fetchAgentsCapabilities]);

    const handleAgentSelect = async (agentName) => {
        setSelectedAgent(agentName);
        setLoading(true);
        setError(null);

        try {
            const result = await fetchSpecificAgentStatus(agentName);
            if (result.success) {
                setAgentDetails(result.data);
            } else {
                setError(result.error);
            }
        } catch (err) {
            setError('Failed to fetch agent details');
        } finally {
            setLoading(false);
        }
    };

    const handleAgentRestart = async (agentName) => {
        setLoading(true);
        setError(null);

        try {
            const result = await restartAgent(agentName);
            if (result.success) {
                // Refresh agent status after restart
                await fetchAgentsStatus();
                if (selectedAgent === agentName) {
                    await handleAgentSelect(agentName);
                }
            } else {
                setError(result.error);
            }
        } catch (err) {
            setError('Failed to restart agent');
        } finally {
            setLoading(false);
        }
    };

    const getStatusColor = (status) => {
        switch (status?.toLowerCase()) {
            case 'active':
            case 'healthy':
            case 'online':
                return 'green';
            case 'degraded':
            case 'warning':
                return 'orange';
            case 'inactive':
            case 'unhealthy':
            case 'offline':
                return 'red';
            default:
                return 'gray';
        }
    };

    const renderAgentList = () => {
        if (!agentsStatus?.agents) {
            return <div className="no-agents">No agents available</div>;
        }

        return (
            <div className="agent-list">
                {Object.entries(agentsStatus.agents).map(([agentName, agentInfo]) => (
                    <div
                        key={agentName}
                        className={`agent-item ${selectedAgent === agentName ? 'selected' : ''}`}
                        onClick={() => handleAgentSelect(agentName)}
                    >
                        <div className="agent-basic-info">
                            <div className="agent-name">{agentName}</div>
                            <div className={`agent-status status-${getStatusColor(agentInfo.status)}`}>
                                {agentInfo.status || 'Unknown'}
                            </div>
                        </div>
                        <div className="agent-actions">
                            <Button
                                variant="secondary"
                                size="small"
                                onClick={(e) => {
                                    e.stopPropagation();
                                    handleAgentRestart(agentName);
                                }}
                                loading={loading}
                            >
                                Restart
                            </Button>
                        </div>
                    </div>
                ))}
            </div>
        );
    };

    const renderAgentDetails = () => {
        if (!selectedAgent) {
            return (
                <div className="agent-details-placeholder">
                    Select an agent to view details
                </div>
            );
        }

        if (loading) {
            return (
                <div className="agent-details-loading">
                    <LoadingSpinner />
                    <span>Loading agent details...</span>
                </div>
            );
        }

        if (error) {
            return <ErrorMessage message={error} />;
        }

        if (!agentDetails) {
            return <div className="no-agent-details">No details available</div>;
        }

        const capabilities = agentsCapabilities?.agents?.[selectedAgent];

        return (
            <div className="agent-details">
                <div className="agent-details-header">
                    <h4>{selectedAgent}</h4>
                    <div className={`agent-status status-${getStatusColor(agentDetails.status)}`}>
                        {agentDetails.status}
                    </div>
                </div>

                <div className="agent-details-content">
                    {capabilities && (
                        <div className="agent-capabilities">
                            <h5>Capabilities</h5>
                            <p className="capability-description">
                                {capabilities.description}
                            </p>
                            <div className="capability-list">
                                {capabilities.capabilities?.map((capability, index) => (
                                    <span key={index} className="capability-tag">
                                        {capability}
                                    </span>
                                ))}
                            </div>
                        </div>
                    )}

                    {agentDetails.details && (
                        <div className="agent-technical-details">
                            <h5>Technical Details</h5>
                            <pre>{JSON.stringify(agentDetails.details, null, 2)}</pre>
                        </div>
                    )}

                    {agentDetails.last_updated && (
                        <div className="agent-metadata">
                            <small>
                                Last updated: {new Date(agentDetails.last_updated).toLocaleString()}
                            </small>
                        </div>
                    )}
                </div>
            </div>
        );
    };

    const renderPerformanceOverview = () => {
        if (!agentsPerformance) return null;

        return (
            <div className="performance-overview">
                <h5>Performance Overview</h5>
                <div className="performance-metrics">
                    <div className="metric">
                        <span className="metric-label">Overall Performance:</span>
                        <span className="metric-value">
                            {agentsPerformance.overall_performance || 'Unknown'}
                        </span>
                    </div>
                    <div className="metric">
                        <span className="metric-label">Total Agents:</span>
                        <span className="metric-value">
                            {agentsPerformance.total_agents_monitored || 0}
                        </span>
                    </div>
                    {agentsPerformance.performance_score && (
                        <div className="metric">
                            <span className="metric-label">Performance Score:</span>
                            <span className="metric-value">
                                {agentsPerformance.performance_score}/100
                            </span>
                        </div>
                    )}
                </div>
            </div>
        );
    };

    return (
        <div className="ai-agent-manager">
            <div className="agent-manager-header">
                <h4>AI Agent Manager</h4>
                <Button
                    variant="secondary"
                    size="small"
                    onClick={() => {
                        fetchAgentsStatus();
                        fetchAgentsPerformance();
                    }}
                    loading={isAiProcessing}
                >
                    Refresh All
                </Button>
            </div>

            {renderPerformanceOverview()}

            <div className="agent-manager-content">
                <div className="agent-list-section">
                    <h5>Available Agents</h5>
                    {renderAgentList()}
                </div>

                <div className="agent-details-section">
                    {renderAgentDetails()}
                </div>
            </div>
        </div>
    );
}

export default AIAgentManager;