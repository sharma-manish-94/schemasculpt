package io.github.sharmanish.schemasculpt.service.linter;

import io.github.sharmanish.schemasculpt.dto.ValidationSuggestion;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.Operation;
import io.swagger.v3.oas.models.PathItem;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import org.springframework.stereotype.Component;

/**
 * Linter rule that ensures operations have at least one success response (2xx or 3xx). Based on
 * Spectral's operation-success-response rule.
 */
@Component
public class ResponseSuccessRule implements LinterRule {

  @Override
  public List<ValidationSuggestion> lint(OpenAPI openApi) {
    List<ValidationSuggestion> suggestions = new ArrayList<>();

    if (openApi.getPaths() == null) {
      return suggestions;
    }

    for (Map.Entry<String, PathItem> pathEntry : openApi.getPaths().entrySet()) {
      String path = pathEntry.getKey();
      PathItem pathItem = pathEntry.getValue();

      for (Map.Entry<PathItem.HttpMethod, Operation> opEntry :
          pathItem.readOperationsMap().entrySet()) {
        PathItem.HttpMethod method = opEntry.getKey();
        Operation operation = opEntry.getValue();

        if (!hasSuccessResponse(operation)) {
          suggestions.add(
              new ValidationSuggestion(
                  String.format(
                      "Operation '%s %s' must have at least one success"
                          + " response (2xx or 3xx).",
                      method, path),
                  "add-success-response",
                  "error",
                  "completeness",
                  Map.of("path", path, "method", method.toString()),
                  true));
        }
      }
    }

    return suggestions;
  }

  private boolean hasSuccessResponse(Operation operation) {
    if (operation.getResponses() == null) {
      return false;
    }

    return operation.getResponses().keySet().stream()
        .anyMatch(
            responseCode -> {
              try {
                int code = Integer.parseInt(responseCode);
                return (code >= 200 && code < 400);
              } catch (NumberFormatException e) {
                // Handle special response codes like 'default'
                return false;
              }
            });
  }
}
