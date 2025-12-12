package io.github.sharma_manish_94.schemasculpt_api.service.linter;

import io.github.sharma_manish_94.schemasculpt_api.dto.ValidationSuggestion;
import io.swagger.v3.oas.models.OpenAPI;
import java.util.List;

/**
 * An interface representing a single linting rule to be applied to an OpenAPI specification.
 */
public interface LinterRule {

  /**
   * Applies the linting rule to the given OpenAPI object.
   *
   * @param openApi The parsed OpenAPI specification.
   * @return A list of suggestions found by this rule. An empty list if no issues are found.
   */
  List<ValidationSuggestion> lint(OpenAPI openApi);
}
