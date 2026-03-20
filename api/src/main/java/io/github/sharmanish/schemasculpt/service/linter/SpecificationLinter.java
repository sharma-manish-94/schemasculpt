package io.github.sharmanish.schemasculpt.service.linter;

import io.github.sharmanish.schemasculpt.dto.ValidationSuggestion;
import io.swagger.v3.oas.models.OpenAPI;
import java.util.List;
import org.springframework.stereotype.Service;

@Service
public class SpecificationLinter {
  private final List<LinterRule> rules;

  public SpecificationLinter(List<LinterRule> rules) {
    this.rules = rules;
  }

  public List<ValidationSuggestion> lint(OpenAPI openAPI) {
    return rules.stream().flatMap(linterRule -> linterRule.lint(openAPI).stream()).toList();
  }
}
