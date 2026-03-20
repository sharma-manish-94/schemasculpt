package io.github.sharmanish.schemasculpt.service.linter;

import io.github.sharmanish.schemasculpt.dto.ValidationSuggestion;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.Operation;
import io.swagger.v3.oas.models.PathItem;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import org.springframework.stereotype.Component;

@Component
public class MissingSummaryRule implements LinterRule {

  @Override
  public List<ValidationSuggestion> lint(final OpenAPI openApi) {
    List<ValidationSuggestion> suggestions = new ArrayList<>();
    if (openApi.getPaths() == null) {
      return Collections.emptyList();
    }

    for (final Map.Entry<String, PathItem> pathEntry : openApi.getPaths().entrySet()) {
      String path = pathEntry.getKey();
      PathItem pathItem = pathEntry.getValue();

      for (final Map.Entry<PathItem.HttpMethod, Operation> opEntry :
          pathItem.readOperationsMap().entrySet()) {
        final PathItem.HttpMethod method = opEntry.getKey();
        final Operation operation = opEntry.getValue();
        if (operation.getSummary() == null || operation.getSummary().isBlank()) {
          String message = String.format("Operation '%s %s' is missing a summary.", method, path);
          Map<String, Object> context =
              Map.of(
                  "path",
                  path,
                  "method",
                  method.toString(),
                  "operationId",
                  operation.getOperationId() != null ? operation.getOperationId() : "unknown");
          suggestions.add(
              new ValidationSuggestion(
                  message, "missing-summary", "warning", "documentation", context, true));
        }
      }
    }
    return suggestions;
  }
}
