package io.github.sharmanish.schemasculpt.dto.analysis;

import java.util.List;
import java.util.Set;

/**
 * Response containing blast radius analysis for a schema change.
 *
 * <p>Provides both summary metrics and detailed breakdown of impact:
 *
 * <ul>
 *   <li>Summary: risk level, percentage, total/affected operation counts
 *   <li>Details: direct dependents, all affected schemas, affected endpoints
 * </ul>
 *
 * @param targetSchema The schema being analyzed
 * @param totalOperations Total number of operations in the specification
 * @param affectedOperations Number of operations affected by the schema change
 * @param percentage Percentage of operations affected (0.0 to 100.0)
 * @param riskLevel Risk assessment: LOW, MEDIUM, HIGH, or CRITICAL
 * @param directDependents Schemas that directly reference the target schema
 * @param allAffectedSchemas All schemas affected (direct + transitive)
 * @param affectedEndpoints List of affected endpoint paths (e.g., "GET /users")
 */
public record BlastRadiusResponse(
    String targetSchema,
    int totalOperations,
    int affectedOperations,
    double percentage,
    RiskLevel riskLevel,
    Set<String> directDependents,
    Set<String> allAffectedSchemas,
    List<String> affectedEndpoints) {

  /** Risk level classification for blast radius impact. */
  public enum RiskLevel {
    LOW,
    MEDIUM,
    HIGH,
    CRITICAL
  }

  /** Creates a BlastRadiusResponse with immutable copies of collections. */
  public BlastRadiusResponse {
    directDependents = directDependents != null ? Set.copyOf(directDependents) : Set.of();
    allAffectedSchemas = allAffectedSchemas != null ? Set.copyOf(allAffectedSchemas) : Set.of();
    affectedEndpoints = affectedEndpoints != null ? List.copyOf(affectedEndpoints) : List.of();
  }
}
