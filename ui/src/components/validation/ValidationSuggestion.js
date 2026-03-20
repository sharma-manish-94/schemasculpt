import React, { useState } from "react";
import LoadingSpinner from "../ui/LoadingSpinner";
import { useSpecStore } from "../../store/specStore";
import CodeDiffViewer from "../../features/editor/components/CodeDiffViewer";
import "./ValidationSuggestion.css";

const ValidationSuggestion = ({
  suggestion,
  sessionId,
  specText,
  additionalActions,
  isAIFriendly = false,
}) => {
  const { suggestCodeFix, isSuggestingFix, suggestFixError, suggestedFix } =
    useSpecStore();

  const [explanation, setExplanation] = useState(null);
  const [isLoadingExplanation, setIsLoadingExplanation] = useState(false);
  const [showExplanation, setShowExplanation] = useState(false);
  const [explanationError, setExplanationError] = useState(null);
  const [showFix, setShowFix] = useState(false);

  // Check if this suggestion is fixable with the new AI-powered fix
  const canSuggestFix =
    suggestion.context?.vulnerableCode && suggestion.context?.language;

  const handleSuggestFix = async () => {
    if (!canSuggestFix) return;

    setShowFix(true); // Show the panel immediately with a loading state
    await suggestCodeFix({
      vulnerableCode: suggestion.context.vulnerableCode,
      language: suggestion.context.language,
      vulnerabilityType: suggestion.ruleId || "general-vulnerability",
    });
  };

  const getSeverityClass = (severity) => {
    switch (severity?.toLowerCase()) {
      case "error":
      case "critical":
        return "suggestion-item severity-error";
      case "warning":
      case "high":
        return "suggestion-item severity-warning";
      case "medium":
      case "info":
        return "suggestion-item severity-info";
      case "low":
        return "suggestion-item severity-low";
      default:
        return "suggestion-item";
    }
  };

  const getSeverityIcon = (severity) => {
    switch (severity?.toLowerCase()) {
      case "error":
      case "critical":
        return "❌";
      case "warning":
      case "high":
        return "⚠️";
      case "info":
      case "medium":
        return "ℹ️";
      case "low":
        return "💡";
      default:
        return "🔹";
    }
  };

  const handleExplainClick = async () => {
    if (showExplanation && explanation) {
      setShowExplanation(false);
      return;
    }

    if (explanation) {
      setShowExplanation(true);
      return;
    }

    setIsLoadingExplanation(true);
    setExplanationError(null);

    try {
      const { getAIExplanation } = await import("../../api/aiService");
      const result = await getAIExplanation(sessionId, suggestion.ruleId, {
        message: suggestion.message,
        context: suggestion.context,
      });

      if (result.success) {
        setExplanation(result.explanation);
        setShowExplanation(true);
      } else {
        setExplanationError(result.error);
      }
    } catch (error) {
      setExplanationError(error.message);
    } finally {
      setIsLoadingExplanation(false);
    }
  };

  return (
    <div className={getSeverityClass(suggestion.severity)}>
      <div className="suggestion-content">
        <div className="suggestion-main">
          <span className="suggestion-icon">
            {isAIFriendly ? "🤖" : getSeverityIcon(suggestion.severity)}
          </span>
          <div className="suggestion-text">
            <p className="suggestion-message">{suggestion.message}</p>
            {suggestion.ruleId && (
              <span className="suggestion-rule-id">{suggestion.ruleId}</span>
            )}
          </div>
        </div>

        <div className="suggestion-actions">
          {canSuggestFix && (
            <button
              onClick={handleSuggestFix}
              disabled={isSuggestingFix}
              className="fix-button suggest-fix"
              title="Suggest a code fix with AI"
            >
              🛠️ Fix
            </button>
          )}
          {suggestion.explainable && (
            <button
              onClick={handleExplainClick}
              disabled={isLoadingExplanation}
              className="explain-button"
              title="Get AI explanation"
            >
              {isLoadingExplanation ? "..." : "❓ Why?"}
            </button>
          )}
          {additionalActions}
        </div>
      </div>

      {showFix && (
        <div className="remediation-panel">
          <div className="remediation-header">
            <h4>AI-Suggested Fix</h4>
            <button onClick={() => setShowFix(false)} title="Close Fix">
              ✕
            </button>
          </div>
          {isSuggestingFix && <LoadingSpinner text="Generating fix..." />}
          {suggestFixError && (
            <div className="error-message">{suggestFixError}</div>
          )}
          {suggestedFix && !isSuggestingFix && (
            <CodeDiffViewer
              originalCode={suggestion.context.vulnerableCode}
              modifiedCode={suggestedFix}
              language={suggestion.context.language}
            />
          )}
        </div>
      )}

      {showExplanation && explanation && (
        <div className="explanation-panel">
          <div className="explanation-header">
            <h4>AI Explanation</h4>
            <button onClick={() => setShowExplanation(false)}>✕</button>
          </div>
          <div className="explanation-body">
            <p>{explanation}</p>
          </div>
        </div>
      )}

      {explanationError && (
        <div className="explanation-error">
          <p>Error: {explanationError}</p>
          <button onClick={() => setExplanationError(null)}>✕</button>
        </div>
      )}
    </div>
  );
};

export default ValidationSuggestion;
