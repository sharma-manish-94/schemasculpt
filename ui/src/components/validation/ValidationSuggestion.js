import React, { useState } from 'react';
import Button from '../ui/Button';
import LoadingSpinner from '../ui/LoadingSpinner';
import { explainValidationIssue } from '../../api/validationService';
import './ValidationSuggestion.css';

const ValidationSuggestion = ({ suggestion, sessionId, specText, additionalActions }) => {
    const [explanation, setExplanation] = useState(null);
    const [isLoadingExplanation, setIsLoadingExplanation] = useState(false);
    const [showExplanation, setShowExplanation] = useState(false);
    const [explanationError, setExplanationError] = useState(null);

    const getSeverityIcon = (severity) => {
        switch (severity) {
            case 'error':
                return '🚨';
            case 'warning':
                return '⚠️';
            case 'info':
                return 'ℹ️';
            default:
                return '💡';
        }
    };

    const getSeverityClass = (severity) => {
        return `suggestion-item severity-${severity || 'info'}`;
    };

    const handleExplainClick = async () => {
        if (explanation) {
            setShowExplanation(!showExplanation);
            return;
        }

        setIsLoadingExplanation(true);
        setExplanationError(null);

        try {
            const explanationRequest = {
                ruleId: suggestion.ruleId,
                message: suggestion.message,
                specText: specText || '',
                category: suggestion.category || 'general',
                context: suggestion.context || {}
            };

            const result = await explainValidationIssue(explanationRequest, sessionId);

            if (result.success) {
                setExplanation(result.data);
                setShowExplanation(true);
            } else {
                setExplanationError(result.error || 'Failed to get explanation');
            }
        } catch (error) {
            setExplanationError('Failed to connect to explanation service');
        } finally {
            setIsLoadingExplanation(false);
        }
    };

    return (
        <div className={getSeverityClass(suggestion.severity)}>
            <div className="suggestion-content">
                <div className="suggestion-main">
                    <span className="severity-icon">{getSeverityIcon(suggestion.severity)}</span>
                    <div className="suggestion-text">
                        <span className="suggestion-message">{suggestion.message}</span>
                        {suggestion.ruleId && (
                            <div className="suggestion-rule">{suggestion.ruleId}</div>
                        )}
                    </div>
                </div>

                <div className="suggestion-actions">
                    {suggestion.explainable && (
                        <button
                            onClick={handleExplainClick}
                            disabled={isLoadingExplanation}
                            className="explain-button"
                            title={explanation ? (showExplanation ? 'Hide explanation' : 'Show explanation') : 'Get AI explanation'}
                        >
                            {isLoadingExplanation ? '⋯' : (explanation ? (showExplanation ? '▼' : '?') : '?')}
                        </button>
                    )}
                    {additionalActions}
                </div>
            </div>

            {showExplanation && explanation && (
                <div className="explanation-panel">
                    <div className="explanation-content">
                        <h4>Explanation</h4>
                        <p>{explanation.explanation}</p>

                        {explanation.relatedBestPractices && explanation.relatedBestPractices.length > 0 && (
                            <div className="best-practices">
                                <h5>Related Best Practices</h5>
                                <ul>
                                    {explanation.relatedBestPractices.map((practice, index) => (
                                        <li key={index}>{practice}</li>
                                    ))}
                                </ul>
                            </div>
                        )}

                        {explanation.exampleSolutions && explanation.exampleSolutions.length > 0 && (
                            <div className="example-solutions">
                                <h5>Example Solutions</h5>
                                <ul>
                                    {explanation.exampleSolutions.map((solution, index) => (
                                        <li key={index}>{solution}</li>
                                    ))}
                                </ul>
                            </div>
                        )}

                        {explanation.additionalResources && explanation.additionalResources.length > 0 && (
                            <div className="additional-resources">
                                <h5>Additional Resources</h5>
                                <ul>
                                    {explanation.additionalResources.map((resource, index) => (
                                        <li key={index}>
                                            {resource.startsWith('http') ? (
                                                <a href={resource} target="_blank" rel="noopener noreferrer">
                                                    {resource}
                                                </a>
                                            ) : (
                                                resource
                                            )}
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        )}

                        {explanation.metadata?.ragSources && explanation.metadata.ragSources.length > 0 && (
                            <div className="knowledge-sources">
                                <h6>Knowledge Sources</h6>
                                <div className="sources-list">
                                    {explanation.metadata.ragSources.map((source, index) => (
                                        <span key={index} className="source-tag">{source}</span>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            )}

            {explanationError && (
                <div className="explanation-error">
                    <span className="error-icon">❌</span>
                    <span>{explanationError}</span>
                </div>
            )}
        </div>
    );
};

export default ValidationSuggestion;