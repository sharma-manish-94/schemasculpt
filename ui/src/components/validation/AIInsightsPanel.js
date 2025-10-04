import React, { useState } from 'react';
import './AIInsightsPanel.css';

/**
 * AI Insights Panel - Displays linter-augmented AI analysis results.
 * Shows higher-order patterns and security insights detected by AI meta-analysis.
 */
const AIInsightsPanel = ({ insights, summary, confidenceScore, onRunAnalysis, isLoading }) => {
    const [expandedInsights, setExpandedInsights] = useState(new Set());

    const toggleInsight = (index) => {
        const newExpanded = new Set(expandedInsights);
        if (newExpanded.has(index)) {
            newExpanded.delete(index);
        } else {
            newExpanded.add(index);
        }
        setExpandedInsights(newExpanded);
    };

    const getSeverityIcon = (severity) => {
        switch (severity) {
            case 'critical': return '🔴';
            case 'high': return '🟠';
            case 'medium': return '🟡';
            case 'low': return '🔵';
            default: return 'ℹ️';
        }
    };

    const getCategoryIcon = (category) => {
        switch (category) {
            case 'security': return '🔐';
            case 'design': return '🎨';
            case 'performance': return '⚡';
            case 'governance': return '📋';
            default: return '🔍';
        }
    };

    const getSeverityClass = (severity) => {
        return `severity-${severity}`;
    };

    if (isLoading) {
        return (
            <div className="ai-insights-panel">
                <div className="ai-insights-header">
                    <h3>🤖 AI Insights</h3>
                </div>
                <div className="ai-insights-loading">
                    <div className="spinner"></div>
                    <p>Analyzing patterns and detecting higher-order issues...</p>
                </div>
            </div>
        );
    }

    if (!insights || insights.length === 0) {
        return (
            <div className="ai-insights-panel">
                <div className="ai-insights-header">
                    <h3>🤖 AI Insights</h3>
                    <button
                        className="run-analysis-button"
                        onClick={onRunAnalysis}
                        disabled={isLoading}
                    >
                        Run AI Analysis
                    </button>
                </div>
                <div className="ai-insights-empty">
                    <p>No AI insights available yet.</p>
                    <p className="ai-insights-subtitle">
                        Click "Run AI Analysis" to get AI-powered pattern detection and security insights.
                    </p>
                </div>
            </div>
        );
    }

    return (
        <div className="ai-insights-panel">
            <div className="ai-insights-header">
                <h3>🤖 AI Insights</h3>
                <div className="ai-insights-meta">
                    <span className="confidence-badge" title={`AI Confidence: ${(confidenceScore * 100).toFixed(0)}%`}>
                        Confidence: {(confidenceScore * 100).toFixed(0)}%
                    </span>
                    <button
                        className="run-analysis-button"
                        onClick={onRunAnalysis}
                        disabled={isLoading}
                    >
                        ↻ Refresh
                    </button>
                </div>
            </div>

            {summary && (
                <div className="ai-insights-summary">
                    <h4>Summary</h4>
                    <p>{summary}</p>
                </div>
            )}

            <div className="ai-insights-list">
                <h4>Detected Patterns ({insights.length})</h4>
                {insights.map((insight, index) => (
                    <div
                        key={index}
                        className={`ai-insight-card ${getSeverityClass(insight.severity)}`}
                    >
                        <div
                            className="ai-insight-header"
                            onClick={() => toggleInsight(index)}
                        >
                            <div className="ai-insight-title">
                                <span className="severity-icon">
                                    {getSeverityIcon(insight.severity)}
                                </span>
                                <span className="category-icon">
                                    {getCategoryIcon(insight.category)}
                                </span>
                                <h5>{insight.title}</h5>
                            </div>
                            <button className="expand-button">
                                {expandedInsights.has(index) ? '▼' : '▶'}
                            </button>
                        </div>

                        {expandedInsights.has(index) && (
                            <div className="ai-insight-details">
                                <p className="insight-description">{insight.description}</p>

                                {insight.affectedPaths && insight.affectedPaths.length > 0 && (
                                    <div className="affected-paths">
                                        <strong>Affected Paths:</strong>
                                        <ul>
                                            {insight.affectedPaths.map((path, i) => (
                                                <li key={i}><code>{path}</code></li>
                                            ))}
                                        </ul>
                                    </div>
                                )}

                                {insight.relatedIssues && insight.relatedIssues.length > 0 && (
                                    <div className="related-issues">
                                        <strong>Related Linter Findings:</strong>
                                        <ul>
                                            {insight.relatedIssues.map((issue, i) => (
                                                <li key={i}><code>{issue}</code></li>
                                            ))}
                                        </ul>
                                    </div>
                                )}

                                <div className="insight-metadata">
                                    <span className="badge badge-severity">{insight.severity}</span>
                                    <span className="badge badge-category">{insight.category}</span>
                                </div>
                            </div>
                        )}
                    </div>
                ))}
            </div>
        </div>
    );
};

export default AIInsightsPanel;
