package io.github.sharmanish.schemasculpt.dto;

import io.github.sharmanish.schemasculpt.dto.ai.JsonPatchOperation;
import java.util.List;

/**
 * Response DTO for AI-powered description quality analysis. Contains quality scores, issues, and
 * JSON Patch operations for improvements.
 */
public record DescriptionAnalysisResponse(
    List<DescriptionQuality> results,
    int overallScore, // Average quality score across all items
    List<JsonPatchOperation> patches // JSON Patch operations to apply all improvements
    ) {
  public enum QualityLevel {
    EXCELLENT, // 90-100
    GOOD, // 70-89
    FAIR, // 50-69
    POOR, // 1-49
    MISSING // 0 (no description)
  }

  public record DescriptionQuality(
      String path, // Same path from request
      int qualityScore, // 0-100
      QualityLevel level, // EXCELLENT, GOOD, FAIR, POOR, MISSING
      List<Issue> issues, // What's wrong with current description
      String suggestedDescription, // AI-improved description
      JsonPatchOperation patch // JSON Patch to apply this improvement
      ) {}

  public record Issue(
      String type, // "completeness", "clarity", "accuracy", "best_practice"
      String severity, // "high", "medium", "low"
      String description // Human-readable issue description
      ) {}
}
