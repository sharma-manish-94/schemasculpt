import { useSpecStore } from "../../../store/specStore";
import React from 'react';

function ValidationPanel() {
    // Get errors, suggestions, isLoading, and applyQuickFix action from the store
    const { errors, suggestions, isLoading, applyQuickFix } = useSpecStore();

    // Define which rules can be auto-fixed vs require AI
    const autoFixableRules = [
        'remove-unused-component',
        'generate-operation-id',
        'use-https',
        'use-https-for-production',
        'remove-trailing-slash',
        'fix-consecutive-slashes',
        'use-kebab-case',
        'replace-underscores-with-hyphens',
        'convert-camelcase-to-kebab',
        'add-success-response'
    ];

    const getFixButtonClass = (ruleId) => {
        if (autoFixableRules.includes(ruleId)) {
            return 'fix-button auto-fix';
        }
        return 'fix-button ai-fix';
    };

    const getFixButtonText = (ruleId) => {
        if (autoFixableRules.includes(ruleId)) {
            return 'Fix';
        }
        return 'AI Fix';
    };

    if (isLoading) {
        return <p className="loading-text">Validating...</p>;
    }

    const hasErrors = errors.length > 0;
    const hasSuggestions = suggestions.length > 0;

    if (!hasErrors && !hasSuggestions) {
        return <p className="no-errors">No validation errors or suggestions found.</p>;
    }

    return (
        <>
            {hasErrors && (
                <div className="result-section">
                    <h3 className="result-title-error">Errors</h3>
                    <ul>{errors.map((err, index) => (<li key={`err-${index}`}>{err.message}</li>))}</ul>
                </div>
            )}
            {hasSuggestions && (
                <div className="result-section">
                    <h3 className="result-title-suggestion">Suggestions</h3>
                    <ul>
                        {suggestions.map((sug, index) => (
                            <li className="suggestion-item" key={`sug-${index}`}>
                                <span className="suggestion-text">{sug.message}</span>
                                {sug.ruleId && (
                                    <button
                                        className={getFixButtonClass(sug.ruleId)}
                                        onClick={() => applyQuickFix(sug)}
                                        title={autoFixableRules.includes(sug.ruleId) ? 'Auto-fix available' : 'AI-powered fix'}
                                    >
                                        {getFixButtonText(sug.ruleId)}
                                    </button>
                                )}
                            </li>
                        ))}
                    </ul>
                </div>
            )}
        </>
    );
}

export default ValidationPanel;