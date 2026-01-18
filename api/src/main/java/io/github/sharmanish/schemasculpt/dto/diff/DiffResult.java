package io.github.sharmanish.schemasculpt.dto.diff;

import java.util.List;

/**
 * Result of comparing two OpenAPI specifications.
 *
 * @param changes              List of individual changes detected
 * @param breakingCount        Number of breaking changes
 * @param dangerousCount       Number of dangerous changes
 * @param safeCount            Number of safe changes
 * @param structuralDriftScore Score indicating overall structural deviation (0.0 to 1.0)
 * @param evolutionSummary     Human-readable summary of the API evolution
 */
public record DiffResult(
    List<DiffEntry> changes,
    int breakingCount,
    int dangerousCount,
    int safeCount,
    double structuralDriftScore,
    String evolutionSummary) {

  /**
   * Creates a DiffResult with an immutable copy of the changes list.
   */
  public DiffResult {
    changes = changes != null ? List.copyOf(changes) : List.of();
  }
}
