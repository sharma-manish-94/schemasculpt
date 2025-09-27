import { useSpecStore } from "../../../store/specStore";
import React from 'react';

function ValidationPanel() {
    // Get errors, suggestions, isLoading, applyQuickFix, and validateCurrentSpec from the store
    const { errors, suggestions, isLoading, applyQuickFix, validateCurrentSpec } = useSpecStore();

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

    // Group suggestions by fix type
    const groupSuggestions = (suggestions) => {
        const autoFixSuggestions = suggestions.filter(sug =>
            sug.ruleId && autoFixableRules.includes(sug.ruleId)
        );
        const aiFixSuggestions = suggestions.filter(sug =>
            sug.ruleId && !autoFixableRules.includes(sug.ruleId)
        );
        const noFixSuggestions = suggestions.filter(sug => !sug.ruleId);

        return { autoFixSuggestions, aiFixSuggestions, noFixSuggestions };
    };

    if (isLoading) {
        return <p className="loading-text">Validating...</p>;
    }

    const hasErrors = errors.length > 0;
    const hasSuggestions = suggestions.length > 0;
    const { autoFixSuggestions, aiFixSuggestions, noFixSuggestions } = groupSuggestions(suggestions);

    if (!hasErrors && !hasSuggestions) {
        return <p className="no-errors">No validation errors or suggestions found.</p>;
    }

    return (
        <>
            <div className="validation-header">
                <div className="validation-counts">
                    {hasErrors && (
                        <span className="count-badge error-count">
                            {errors.length} Error{errors.length !== 1 ? 's' : ''}
                        </span>
                    )}
                    {hasSuggestions && (
                        <span className="count-badge suggestion-count">
                            {suggestions.length} Suggestion{suggestions.length !== 1 ? 's' : ''}
                        </span>
                    )}
                    {!hasErrors && !hasSuggestions && (
                        <span className="count-badge success-count">All Clear</span>
                    )}
                </div>
                <button
                    className="refresh-button"
                    onClick={validateCurrentSpec}
                    disabled={isLoading}
                    title="Refresh validation"
                >
                    {isLoading ? '⟳' : '↻'} Refresh
                </button>
            </div>

            {hasErrors && (
                <div className="result-section">
                    <h3 className="result-title-error">Errors</h3>
                    <ul>{errors.map((err, index) => (<li key={`err-${index}`}>{err.message}</li>))}</ul>
                </div>
            )}
            {hasSuggestions && (
                <>
                    {autoFixSuggestions.length > 0 && (
                        <div className="result-section">
                            <h3 className="result-title-autofix">
                                <span className="fix-type-icon">⚡</span>
                                Auto-Fix Suggestions ({autoFixSuggestions.length})
                            </h3>
                            <ul>
                                {autoFixSuggestions.map((sug, index) => (
                                    <li className="suggestion-item" key={`auto-${index}`}>
                                        <span className="suggestion-text">{sug.message}</span>
                                        <button
                                            className={getFixButtonClass(sug.ruleId)}
                                            onClick={() => applyQuickFix(sug)}
                                            title="Auto-fix available"
                                        >
                                            {getFixButtonText(sug.ruleId)}
                                        </button>
                                    </li>
                                ))}
                            </ul>
                        </div>
                    )}

                    {aiFixSuggestions.length > 0 && (
                        <div className="result-section">
                            <h3 className="result-title-aifix">
                                <span className="fix-type-icon">🤖</span>
                                AI-Fix Suggestions ({aiFixSuggestions.length})
                            </h3>
                            <ul>
                                {aiFixSuggestions.map((sug, index) => (
                                    <li className="suggestion-item" key={`ai-${index}`}>
                                        <span className="suggestion-text">{sug.message}</span>
                                        <button
                                            className={getFixButtonClass(sug.ruleId)}
                                            onClick={() => applyQuickFix(sug)}
                                            title="AI-powered fix"
                                        >
                                            {getFixButtonText(sug.ruleId)}
                                        </button>
                                    </li>
                                ))}
                            </ul>
                        </div>
                    )}

                    {noFixSuggestions.length > 0 && (
                        <div className="result-section">
                            <h3 className="result-title-suggestion">
                                <span className="fix-type-icon">💡</span>
                                General Suggestions ({noFixSuggestions.length})
                            </h3>
                            <ul>
                                {noFixSuggestions.map((sug, index) => (
                                    <li className="suggestion-item" key={`general-${index}`}>
                                        <span className="suggestion-text">{sug.message}</span>
                                    </li>
                                ))}
                            </ul>
                        </div>
                    )}
                </>
            )}
        </>
    );
}

export default ValidationPanel;