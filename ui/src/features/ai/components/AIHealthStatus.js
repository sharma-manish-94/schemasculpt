import React, { useState, useEffect } from 'react';
import { useSpecStore } from '../../../store/specStore';
import Button from '../../../components/ui/Button';
import LoadingSpinner from '../../../components/ui/LoadingSpinner';
import ErrorMessage from '../../../components/ui/ErrorMessage';

function AIHealthStatus() {
    const {
        checkAiHealth,
        aiHealthStatus,
        isAiProcessing
    } = useSpecStore();

    const [lastChecked, setLastChecked] = useState(null);
    const [autoRefresh, setAutoRefresh] = useState(false);

    useEffect(() => {
        checkAiHealth().then(() => {
            setLastChecked(new Date());
        });
    }, [checkAiHealth]);

    useEffect(() => {
        if (!autoRefresh) return;

        const interval = setInterval(() => {
            checkAiHealth().then(() => {
                setLastChecked(new Date());
            });
        }, 30000); // Check every 30 seconds

        return () => clearInterval(interval);
    }, [autoRefresh, checkAiHealth]);

    const handleManualRefresh = async () => {
        await checkAiHealth();
        setLastChecked(new Date());
    };

    const getStatusColor = (status) => {
        if (!status) return 'gray';

        switch (status.toLowerCase()) {
            case 'healthy':
            case 'online':
            case 'available':
                return 'green';
            case 'degraded':
            case 'warning':
                return 'orange';
            case 'unhealthy':
            case 'offline':
            case 'unavailable':
                return 'red';
            default:
                return 'gray';
        }
    };

    const renderHealthMetrics = () => {
        if (!aiHealthStatus) {
            return <div className="health-placeholder">No health data available</div>;
        }

        return (
            <div className="health-metrics">
                <div className="metric-card">
                    <div className="metric-label">Overall Status</div>
                    <div className={`metric-value status-${getStatusColor(aiHealthStatus.status)}`}>
                        {aiHealthStatus.status || 'Unknown'}
                    </div>
                </div>

                {aiHealthStatus.response_time && (
                    <div className="metric-card">
                        <div className="metric-label">Response Time</div>
                        <div className="metric-value">
                            {aiHealthStatus.response_time}ms
                        </div>
                    </div>
                )}

                {aiHealthStatus.model_info && (
                    <div className="metric-card">
                        <div className="metric-label">Model</div>
                        <div className="metric-value">
                            {aiHealthStatus.model_info.name || 'Unknown'}
                        </div>
                    </div>
                )}

                {aiHealthStatus.version && (
                    <div className="metric-card">
                        <div className="metric-label">Version</div>
                        <div className="metric-value">
                            {aiHealthStatus.version}
                        </div>
                    </div>
                )}
            </div>
        );
    };

    const renderServiceDetails = () => {
        if (!aiHealthStatus?.services) {
            return null;
        }

        return (
            <div className="service-details">
                <h4>Service Status</h4>
                <div className="service-list">
                    {Object.entries(aiHealthStatus.services).map(([serviceName, serviceStatus]) => (
                        <div key={serviceName} className="service-item">
                            <div className="service-name">{serviceName}</div>
                            <div className={`service-status status-${getStatusColor(serviceStatus.status)}`}>
                                {serviceStatus.status || 'Unknown'}
                            </div>
                            {serviceStatus.details && (
                                <div className="service-details-text">
                                    {serviceStatus.details}
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            </div>
        );
    };

    return (
        <div className="ai-health-status">
            <div className="health-header">
                <h4>AI Service Health</h4>
                <div className="health-controls">
                    <label className="auto-refresh-toggle">
                        <input
                            type="checkbox"
                            checked={autoRefresh}
                            onChange={(e) => setAutoRefresh(e.target.checked)}
                        />
                        Auto Refresh (30s)
                    </label>
                    <Button
                        variant="secondary"
                        size="small"
                        onClick={handleManualRefresh}
                        loading={isAiProcessing}
                    >
                        Refresh
                    </Button>
                </div>
            </div>

            {isAiProcessing ? (
                <div className="health-loading">
                    <LoadingSpinner />
                    <span>Checking AI service health...</span>
                </div>
            ) : (
                <>
                    {renderHealthMetrics()}
                    {renderServiceDetails()}
                </>
            )}

            {lastChecked && (
                <div className="health-footer">
                    <small>
                        Last checked: {lastChecked.toLocaleTimeString()}
                    </small>
                </div>
            )}

            {aiHealthStatus?.error && (
                <div className="health-error">
                    <ErrorMessage message={aiHealthStatus.error} />
                </div>
            )}
        </div>
    );
}

export default AIHealthStatus;