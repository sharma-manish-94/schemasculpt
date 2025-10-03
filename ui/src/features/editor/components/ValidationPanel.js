import { useSpecStore } from "../../../store/specStore";
import React, { useMemo, useCallback } from 'react';
import ValidationSuggestion from '../../../components/validation/ValidationSuggestion';
import { groupSuggestionsByCategory, getSuggestionsSummary } from '../../../utils/suggestionGrouping';

const ValidationPanel = React.memo(() => {
    // Get errors, suggestions, isLoading, applyQuickFix, validateCurrentSpec, specText, and sessionId from the store
    const { errors, suggestions, isLoading, applyQuickFix, validateCurrentSpec, specText, sessionId } = useSpecStore();

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
            return '⚡'; // Lightning bolt for auto-fix
        }
        return '✨'; // Sparkles for AI-fix
    };

    const getFixButtonTitle = (ruleId) => {
        if (autoFixableRules.includes(ruleId)) {
            return 'Auto-fix this issue';
        }
        return 'AI-powered fix';
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

    // Group suggestions by category
    const groupedByCategory = useMemo(() =>
        groupSuggestionsByCategory(suggestions),
        [suggestions]
    );

    const suggestionsSummary = useMemo(() =>
        getSuggestionsSummary(suggestions),
        [suggestions]
    );

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
                    {suggestionsSummary.byCategory.Security > 0 && (
                        <span className="count-badge security-count" title="Security-related suggestions">
                            🔐 {suggestionsSummary.byCategory.Security} Security
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
                            <div className="suggestions-list">
                                {autoFixSuggestions.map((sug, index) => {
                                    // Convert to ValidationSuggestion format
                                    const suggestion = {
                                        message: sug.message,
                                        ruleId: sug.ruleId,
                                        severity: 'info',
                                        context: sug.context || {},
                                        explainable: true
                                    };

                                    const fixButton = (
                                        <button
                                            className={getFixButtonClass(sug.ruleId)}
                                            onClick={() => applyQuickFix(sug)}
                                            title={getFixButtonTitle(sug.ruleId)}
                                        >
                                            {getFixButtonText(sug.ruleId)}
                                        </button>
                                    );

                                    return (
                                        <ValidationSuggestion
                                            key={`auto-${index}`}
                                            suggestion={suggestion}
                                            sessionId={sessionId}
                                            specText={specText}
                                            additionalActions={fixButton}
                                        />
                                    );
                                })}
                            </div>
                        </div>
                    )}

                    {aiFixSuggestions.length > 0 && (
                        <div className="result-section">
                            <h3 className="result-title-aifix">
                                <span className="fix-type-icon">🤖</span>
                                AI-Fix Suggestions ({aiFixSuggestions.length})
                            </h3>
                            <div className="suggestions-list">
                                {aiFixSuggestions.map((sug, index) => {
                                    // Convert to ValidationSuggestion format
                                    const suggestion = {
                                        message: sug.message,
                                        ruleId: sug.ruleId,
                                        severity: 'warning',
                                        context: sug.context || {},
                                        explainable: true
                                    };

                                    const fixButton = (
                                        <button
                                            className={getFixButtonClass(sug.ruleId)}
                                            onClick={() => applyQuickFix(sug)}
                                            title={getFixButtonTitle(sug.ruleId)}
                                        >
                                            {getFixButtonText(sug.ruleId)}
                                        </button>
                                    );

                                    return (
                                        <ValidationSuggestion
                                            key={`ai-${index}`}
                                            suggestion={suggestion}
                                            sessionId={sessionId}
                                            specText={specText}
                                            additionalActions={fixButton}
                                        />
                                    );
                                })}
                            </div>
                        </div>
                    )}

                    {noFixSuggestions.length > 0 && (
                        <div className="result-section">
                            <h3 className="result-title-suggestion">
                                <span className="fix-type-icon">💡</span>
                                General Suggestions ({noFixSuggestions.length})
                            </h3>
                            <div className="suggestions-list">
                                {noFixSuggestions.map((sug, index) => {
                                    // Convert to ValidationSuggestion format
                                    const suggestion = {
                                        message: sug.message,
                                        ruleId: sug.ruleId || 'general-suggestion',
                                        severity: 'info',
                                        context: sug.context || {},
                                        explainable: true
                                    };
                                    return (
                                        <ValidationSuggestion
                                            key={`general-${index}`}
                                            suggestion={suggestion}
                                            sessionId={sessionId}
                                            specText={specText}
                                        />
                                    );
                                })}
                            </div>
                        </div>
                    )}
                </>
            )}
        </>
    );
});

ValidationPanel.displayName = 'ValidationPanel';

export default ValidationPanel;