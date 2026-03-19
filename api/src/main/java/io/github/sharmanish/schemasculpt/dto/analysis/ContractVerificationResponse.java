package io.github.sharmanish.schemasculpt.dto.analysis;

import java.util.List;

public record ContractVerificationResponse(
    boolean is_synchronized, List<ContractIssue> issues, String summary) {
  public record ContractIssue(
      String type, // PARAMETER, SCHEMA
      String severity, // INFO, WARNING, ERROR
      String description,
      String spec_value,
      String code_value) {}
}
