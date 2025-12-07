import { useSpecStore } from "../../../store/specStore";
import React, { useMemo, useCallback, useState } from 'react';
import ValidationSuggestion from '../../../components/validation/ValidationSuggestion';
import AIInsightsPanel from '../../../components/validation/AIInsightsPanel';
import DescriptionQualityPanel from '../../../components/validation/DescriptionQualityPanel';
import { groupSuggestionsByCategory, getSuggestionsSummary } from '../../../utils/suggestionGrouping';

const ValidationPanel = React.memo(() => {
    // Collapsible section state
    const [expandedSections, setExpandedSections] = useState({
        errors: true, // Errors always expanded by default
        aiFriendly: false,
        autoFix: false,
        aiFix: false,
        noFix: false,
        aiInsights: false,
        descriptionQuality: false
    });

    // Toggle individual section
    const toggleSection = (section) => {
        setExpandedSections(prev => ({
            ...prev,
            [section]: !prev[section]
        }));
    };

    // Expand all sections
    const expandAll = () => {
        setExpandedSections({
            errors: true,
            aiFriendly: true,
            autoFix: true,
            aiFix: true,
            noFix: true,
            aiInsights: true,
            descriptionQuality: true
        });
    };

    // Collapse all sections
    const collapseAll = () => {
        setExpandedSections({
            errors: true, // Keep errors expanded
            aiFriendly: false,
            autoFix: false,
            aiFix: false,
            noFix: false,
            aiInsights: false,
            descriptionQuality: false
        });
    };

    // Get errors, suggestions, isLoading, applyQuickFix, validateCurrentSpec, specText, and sessionId from the store
    const {
        errors,
        suggestions,
        isLoading,
        applyQuickFix,
        validateCurrentSpec,
        specText,
        sessionId,
        aiInsights,
        aiSummary,
        aiConfidenceScore,
        isAIAnalysisLoading,
        runAIMetaAnalysis,
        descriptionQuality,
        isDescriptionAnalysisLoading,
        runDescriptionAnalysis,
        applyDescriptionPatches
    } = useSpecStore();

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
        'add-success-response',
        'create-missing-schema',
        'add-missing-description'
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

    // Group suggestions by fix type and category
    const groupSuggestions = (suggestions) => {
        const autoFixSuggestions = suggestions.filter(sug =>
            sug.ruleId && autoFixableRules.includes(sug.ruleId) && sug.category !== 'ai-friendliness'
        );
        const aiFixSuggestions = suggestions.filter(sug =>
            sug.ruleId && !autoFixableRules.includes(sug.ruleId) && sug.category !== 'ai-friendliness'
        );
        const noFixSuggestions = suggestions.filter(sug => !sug.ruleId && sug.category !== 'ai-friendliness');

        // NEW: Separate AI-friendly suggestions
        const aiFriendlySuggestions = suggestions.filter(sug => sug.category === 'ai-friendliness');

        return { autoFixSuggestions, aiFixSuggestions, noFixSuggestions, aiFriendlySuggestions };
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

    if (!hasErrors && !hasSuggestions) {
        return <p className="no-errors">No validation errors or suggestions found.</p>;
    }

    const { autoFixSuggestions, aiFixSuggestions, noFixSuggestions, aiFriendlySuggestions } = groupSuggestions(suggestions);

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
                    {aiFriendlySuggestions.length > 0 && (
                        <span className="count-badge ai-friendly-count" title="AI-friendliness suggestions">
                            🤖 {aiFriendlySuggestions.length} AI-Friendly
                        </span>
                    )}
                    {!hasErrors && !hasSuggestions && (
                        <span className="count-badge success-count">All Clear</span>
                    )}
                </div>
                <div className="validation-actions">
                    <button
                        className="toggle-button"
                        onClick={expandAll}
                        title="Expand all sections"
                    >
                        ▼ Expand All
                    </button>
                    <button
                        className="toggle-button"
                        onClick={collapseAll}
                        title="Collapse all sections"
                    >
                        ▲ Collapse All
                    </button>
                    <button
                        className="refresh-button"
                        onClick={validateCurrentSpec}
                        disabled={isLoading}
                        title="Refresh validation"
                    >
                        {isLoading ? '⟳' : '↻'} Refresh
                    </button>
                </div>
            </div>

            {hasErrors && (
                <div className="result-section">
                    <h3 className="result-title-error">Errors</h3>
                    <ul>{errors.map((err, index) => (<li key={`err-${index}`}>{err.message}</li>))}</ul>
                </div>
            )}
            {hasSuggestions && (
                <>
                    {/* AI-Friendly Suggestions Section - Highlighted Separately */}
                    {aiFriendlySuggestions.length > 0 && (
                        <div className="result-section ai-friendly-section">
                            <h3
                                className="result-title-ai-friendly collapsible-title"
                                onClick={() => toggleSection('aiFriendly')}
                            >
                                <span className="collapse-icon">{expandedSections.aiFriendly ? '▼' : '▶'}</span>
                                <span className="fix-type-icon">🤖</span>
                                AI-Friendly Suggestions ({aiFriendlySuggestions.length})
                                <span className="ai-badge">MCP Ready</span>
                            </h3>
                            {expandedSections.aiFriendly && (
                            <div className="suggestions-list">
                                {aiFriendlySuggestions.map((sug, index) => {
                                    const suggestion = {
                                        message: sug.message,
                                        ruleId: sug.ruleId,
                                        severity: sug.severity || 'info',
                                        context: sug.context || {},
                                        explainable: true
                                    };

                                    return (
                                        <ValidationSuggestion
                                            key={`ai-friendly-${index}`}
                                            suggestion={suggestion}
                                            sessionId={sessionId}
                                            specText={specText}
                                            isAIFriendly={true}
                                        />
                                    );
                                })}
                            </div>
                            )}
                        </div>
                    )}

                    {autoFixSuggestions.length > 0 && (
                        <div className="result-section">
                            <h3
                                className="result-title-autofix collapsible-title"
                                onClick={() => toggleSection('autoFix')}
                            >
                                <span className="collapse-icon">{expandedSections.autoFix ? '▼' : '▶'}</span>
                                <span className="fix-type-icon">⚡</span>
                                Auto-Fix Suggestions ({autoFixSuggestions.length})
                            </h3>
                            {expandedSections.autoFix && (
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
                            )}
                        </div>
                    )}

                    {aiFixSuggestions.length > 0 && (
                        <div className="result-section">
                            <h3
                                className="result-title-aifix collapsible-title"
                                onClick={() => toggleSection('aiFix')}
                            >
                                <span className="collapse-icon">{expandedSections.aiFix ? '▼' : '▶'}</span>
                                <span className="fix-type-icon">✨</span>
                                AI-Fix Suggestions ({aiFixSuggestions.length})
                            </h3>
                            {expandedSections.aiFix && (
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
                            )}
                        </div>
                    )}

                    {noFixSuggestions.length > 0 && (
                        <div className="result-section">
                            <h3
                                className="result-title-suggestion collapsible-title"
                                onClick={() => toggleSection('noFix')}
                            >
                                <span className="collapse-icon">{expandedSections.noFix ? '▼' : '▶'}</span>
                                <span className="fix-type-icon">💡</span>
                                General Suggestions ({noFixSuggestions.length})
                            </h3>
                            {expandedSections.noFix && (
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
                            )}
                        </div>
                    )}
                </>
            )}

            {/* AI Insights Panel */}
            <div className="result-section ai-insights-section">
                <h3
                    className="result-title-ai-insights collapsible-title"
                    onClick={() => toggleSection('aiInsights')}
                >
                    <span className="collapse-icon">{expandedSections.aiInsights ? '▼' : '▶'}</span>
                    <span className="fix-type-icon">🧠</span>
                    AI Insights
                </h3>
                {expandedSections.aiInsights && (
                    <AIInsightsPanel
                        insights={aiInsights}
                        summary={aiSummary}
                        confidenceScore={aiConfidenceScore}
                        onRunAnalysis={runAIMetaAnalysis}
                        isLoading={isAIAnalysisLoading}
                    />
                )}
            </div>

            {/* Description Quality Panel */}
            <div className="result-section description-quality-section">
                <div className="section-header">
                    <h3
                        className="result-title-description collapsible-title"
                        onClick={() => toggleSection('descriptionQuality')}
                    >
                        <span className="collapse-icon">{expandedSections.descriptionQuality ? '▼' : '▶'}</span>
                        <span className="fix-type-icon">📝</span>
                        Description Quality Analysis
                    </h3>
                    {expandedSections.descriptionQuality && (
                        <button
                            className="analyze-descriptions-btn"
                            onClick={runDescriptionAnalysis}
                            disabled={isDescriptionAnalysisLoading || !sessionId}
                            title="Analyze description quality"
                        >
                            {isDescriptionAnalysisLoading ? '⟳ Analyzing...' : '🔍 Analyze Descriptions'}
                        </button>
                    )}
                </div>
                {expandedSections.descriptionQuality && (
                    <DescriptionQualityPanel
                        results={descriptionQuality?.results || []}
                        overallScore={descriptionQuality?.overallScore || 0}
                        patches={descriptionQuality?.patches || []}
                        onApplyPatches={applyDescriptionPatches}
                        isLoading={isDescriptionAnalysisLoading}
                    />
                )}
            </div>
        </>
    );
});

ValidationPanel.displayName = 'ValidationPanel';

export default ValidationPanel;