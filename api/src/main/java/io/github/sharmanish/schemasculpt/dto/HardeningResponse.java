package io.github.sharmanish.schemasculpt.dto;

import com.fasterxml.jackson.annotation.JsonInclude;
import java.util.List;
import java.util.Map;

@JsonInclude(JsonInclude.Include.NON_EMPTY)
public record HardeningResponse(
    String path,
    String method,
    List<String> appliedPatterns,
    Map<String, Object> changes,
    List<String> warnings,
    boolean success) {
  public HardeningResponse(String path, String method, List<String> appliedPatterns) {
    this(path, method, appliedPatterns, Map.of(), List.of(), true);
  }
}
