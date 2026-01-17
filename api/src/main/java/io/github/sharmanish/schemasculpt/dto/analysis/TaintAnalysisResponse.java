package io.github.sharmanish.schemasculpt.dto.analysis;

import java.util.List;

/**
 * Response containing taint analysis results for sensitive data leakage detection.
 *
 * @param vulnerabilities List of detected taint vulnerabilities
 */
public record TaintAnalysisResponse(List<TaintVulnerability> vulnerabilities) {

  /**
   * Creates a TaintAnalysisResponse with an immutable copy of vulnerabilities.
   */
  public TaintAnalysisResponse {
    vulnerabilities = vulnerabilities != null ? List.copyOf(vulnerabilities) : List.of();
  }

  /**
   * Represents a single taint vulnerability where sensitive data may leak.
   *
   * @param endpoint    The affected endpoint (e.g., "GET /users/{id}")
   * @param severity    Severity level using sealed type hierarchy
   * @param description Human-readable description of the vulnerability
   * @param leakedData  Trail showing the data flow (e.g., "Schema: User -> Property: ssn")
   */
  public record TaintVulnerability(
      String endpoint,
      Severity severity,
      String description,
      String leakedData) {}
}
