package io.github.sharmanish.schemasculpt.dto.analysis;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import java.util.List;

@JsonIgnoreProperties(ignoreUnknown = true)
public record SpecCorrelationResponse(
    Boolean matched,
    Integer candidates_found,
    BestMatch best_match
) {
  public record BestMatch(
      String handler,
      String qualified_name,
      String file,
      Integer start_line,
      Integer end_line,
      String language,
      String repo,
      Double confidence,
      String confidence_reason,
      List<String> callees,
      String code_snippet
  ) {}
}
