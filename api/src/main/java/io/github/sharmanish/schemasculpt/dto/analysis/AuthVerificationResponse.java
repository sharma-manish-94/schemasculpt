package io.github.sharmanish.schemasculpt.dto.analysis;

import java.util.List;

public record AuthVerificationResponse(
    boolean auth_synchronized, List<AuthIssue> issues, String spec_auth, String code_auth) {
  public record AuthIssue(String severity, String description) {}
}
