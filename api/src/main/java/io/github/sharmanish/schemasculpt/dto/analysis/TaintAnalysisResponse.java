package io.github.sharmanish.schemasculpt.dto.analysis;

import java.util.List;

public record TaintAnalysisResponse(
    List<TaintVulnerability> vulnerabilities
) {
  public record TaintVulnerability(
      String endpoint,      // e.g., "GET /users/{id}"
      String severity,      // e.g., "CRITICAL"
      String description,   // e.g., "Returns PII (SSN) without security"
      String leakedData     // e.g., "Schema: User -> Property: ssn"
  ) {
  }
}
