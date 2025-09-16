import React from 'react';
import { useSpecStore } from '../../../store/specStore'; // Connect to our store

function ValidationPanel() {
    // Get errors, suggestions, isLoading, and applyQuickFix action from the store
    const { errors, suggestions, isLoading, applyQuickFix } = useSpecStore();

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
                                {sug.message}
                                {sug.ruleId && (
                                    <button className="fix-button" onClick={() => applyQuickFix(sug)}>Fix</button>
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