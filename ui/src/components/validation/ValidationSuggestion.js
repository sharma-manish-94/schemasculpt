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

  const [explanation] = useState(null);
  const [isLoadingExplanation] = useState(false);
  const [showExplanation] = useState(false);
  const [explanationError] = useState(null);
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
    // ... (same as before)
  };

  // ... (useEffect for cache remains the same)

  const handleExplainClick = async () => {
    // ... (same as before)
  };

  return (
    <div className={getSeverityClass(suggestion.severity)}>
      <div className="suggestion-content">
        <div className="suggestion-main">
          {/* ... (icon and text same as before) */}
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
              {/* ... */}
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
        <div className="explanation-panel">{/* ... (same as before) */}</div>
      )}

      {explanationError && (
        <div className="explanation-error">{/* ... (same as before) */}</div>
      )}
    </div>
  );
};

export default ValidationSuggestion;
