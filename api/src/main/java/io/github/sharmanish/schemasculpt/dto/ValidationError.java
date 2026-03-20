package io.github.sharmanish.schemasculpt.dto;

import com.fasterxml.jackson.annotation.JsonInclude;
import java.util.Map;

@JsonInclude(JsonInclude.Include.NON_EMPTY)
public record ValidationError(
    String message, String severity, String path, Map<String, Object> context) {
  public ValidationError(String message) {
    this(message, "error", null, Map.of());
  }

  public ValidationError(String message, String severity) {
    this(message, severity, null, Map.of());
  }

  public ValidationError(String message, String severity, String path) {
    this(message, severity, path, Map.of());
  }
}
