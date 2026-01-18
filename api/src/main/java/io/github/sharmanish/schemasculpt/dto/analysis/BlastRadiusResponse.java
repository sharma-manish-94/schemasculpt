package io.github.sharmanish.schemasculpt.dto.analysis;

import java.util.List;

/**
 * Response containing blast radius analysis for a schema change.
 *
 * @param targetSchema     The schema being analyzed
 * @param totalEndpoints   Total number of endpoints in the specification
 * @param affectedCount    Number of endpoints affected by the schema change
 * @param impactPercentage Percentage of endpoints affected (0.0 to 100.0)
 * @param riskLevel        Risk assessment: LOW, MEDIUM, or CRITICAL
 * @param affectedPaths    List of affected endpoint paths
 */
public record BlastRadiusResponse(
    String targetSchema,
    int totalEndpoints,
    int affectedCount,
    double impactPercentage,
    RiskLevel riskLevel,
    List<String> affectedPaths) {

  /**
   * Risk level classification for blast radius impact.
   */
  public enum RiskLevel {
    LOW,
    MEDIUM,
    CRITICAL
  }

  /**
   * Creates a BlastRadiusResponse with an immutable copy of the affected paths list.
   */
  public BlastRadiusResponse {
    affectedPaths = affectedPaths != null ? List.copyOf(affectedPaths) : List.of();
  }
}
