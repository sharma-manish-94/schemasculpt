package io.github.sharmanish.schemasculpt.service.linter;

import io.github.sharmanish.schemasculpt.dto.ValidationSuggestion;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.Operation;
import io.swagger.v3.oas.models.PathItem;
import io.swagger.v3.oas.models.security.SecurityRequirement;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import org.springframework.stereotype.Component;

/**
 * Linter rule that checks if operations have appropriate security requirements. Ensures API
 * security is properly defined and applied.
 */
@Component
public class SecurityRequirementsRule implements LinterRule {

  @Override
  public List<ValidationSuggestion> lint(OpenAPI openApi) {
    List<ValidationSuggestion> suggestions = new ArrayList<>();

    // Check if security schemes are defined
    boolean hasSecuritySchemes =
        openApi.getComponents() != null
            && openApi.getComponents().getSecuritySchemes() != null
            && !openApi.getComponents().getSecuritySchemes().isEmpty();

    if (!hasSecuritySchemes) {
      suggestions.add(
          new ValidationSuggestion(
              "API should define security schemes in components.securitySchemes.",
              "add-security-schemes",
              "warning",
              "security",
              Map.of("location", "components.securitySchemes"),
              true));
    }

    // Check operations for security requirements
    if (openApi.getPaths() != null) {
      suggestions.addAll(checkOperationSecurity(openApi, hasSecuritySchemes));
    }

    return suggestions;
  }

  private List<ValidationSuggestion> checkOperationSecurity(
      OpenAPI openApi, boolean hasSecuritySchemes) {
    List<ValidationSuggestion> suggestions = new ArrayList<>();

    // Check if global security is defined
    boolean hasGlobalSecurity = openApi.getSecurity() != null && !openApi.getSecurity().isEmpty();

    for (Map.Entry<String, PathItem> pathEntry : openApi.getPaths().entrySet()) {
      String path = pathEntry.getKey();
      PathItem pathItem = pathEntry.getValue();

      for (Map.Entry<PathItem.HttpMethod, Operation> opEntry :
          pathItem.readOperationsMap().entrySet()) {
        PathItem.HttpMethod method = opEntry.getKey();
        Operation operation = opEntry.getValue();

        boolean hasOperationSecurity =
            operation.getSecurity() != null && !operation.getSecurity().isEmpty();

        // Check if operation has security (either global or operation-level)
        if (!hasGlobalSecurity && !hasOperationSecurity && hasSecuritySchemes) {
          // Skip GET operations that might be public
          if (!method.equals(PathItem.HttpMethod.GET)) {
            suggestions.add(
                new ValidationSuggestion(
                    String.format(
                        "Operation '%s %s' should have security" + " requirements defined.",
                        method, path),
                    "add-operation-security",
                    "error",
                    "security",
                    Map.of("path", path, "method", method.toString()),
                    true));
          }
        }

        // Check if security requirements reference valid schemes
        if (hasOperationSecurity && hasSecuritySchemes) {
          for (SecurityRequirement securityRequirement : operation.getSecurity()) {
            for (String schemeName : securityRequirement.keySet()) {
              if (!openApi.getComponents().getSecuritySchemes().containsKey(schemeName)) {
                suggestions.add(
                    new ValidationSuggestion(
                        String.format(
                            "Operation '%s %s' references undefined" + " security scheme '%s'.",
                            method, path, schemeName),
                        "invalid-security-reference",
                        "error",
                        "security",
                        Map.of("path", path, "method", method.toString(), "scheme", schemeName),
                        true));
              }
            }
          }
        }
      }
    }

    return suggestions;
  }
}
