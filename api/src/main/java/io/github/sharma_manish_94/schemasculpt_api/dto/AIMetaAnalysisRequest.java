package io.github.sharma_manish_94.schemasculpt_api.dto;

import java.util.List;

/**
 * Request DTO for AI meta-analysis of linter findings.
 * Sends the specification along with structured linter issues to the AI service
 * for higher-level pattern detection and security analysis.
 */
public record AIMetaAnalysisRequest(
        String specText,
        List<ValidationError> errors,
        List<ValidationSuggestion> suggestions
) {
}
