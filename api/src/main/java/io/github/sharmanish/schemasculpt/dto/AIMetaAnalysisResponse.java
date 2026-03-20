package io.github.sharmanish.schemasculpt.dto;

import com.fasterxml.jackson.annotation.JsonInclude;
import java.util.List;

/**
 * Response DTO for AI meta-analysis results. Contains high-level insights derived from linter
 * findings and AI reasoning.
 */
@JsonInclude(JsonInclude.Include.NON_NULL)
public record AIMetaAnalysisResponse(
    List<AIInsight> insights, String summary, double confidenceScore) {
  /** Individual AI-generated insight about the specification. */
  @JsonInclude(JsonInclude.Include.NON_NULL)
  public record AIInsight(
      String title,
      String description,
      String severity, // "critical", "high", "medium", "low", "info"
      String category, // "security", "design", "performance", "governance"
      List<String> affectedPaths,
      List<String> relatedIssues // References to original linter issue ruleIds
      ) {}
}
