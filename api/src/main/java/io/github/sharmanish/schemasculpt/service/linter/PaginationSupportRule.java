package io.github.sharmanish.schemasculpt.service.linter;

import io.github.sharmanish.schemasculpt.dto.ValidationSuggestion;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.Operation;
import io.swagger.v3.oas.models.parameters.Parameter;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import org.springframework.stereotype.Component;

/**
 * Linter rule that checks for pagination support in list/collection endpoints.
 *
 * <p>AI agents struggle with "chatty" workflows that require many sequential calls. List endpoints
 * without pagination force agents to fetch all data at once, causing performance issues and
 * timeouts.
 */
@Component
public class PaginationSupportRule implements LinterRule {

  private static final String RULE_ID = "pagination-support";

  @Override
  public List<ValidationSuggestion> lint(OpenAPI openApi) {
    List<ValidationSuggestion> suggestions = new ArrayList<>();

    if (openApi.getPaths() == null) {
      return suggestions;
    }

    openApi
        .getPaths()
        .forEach(
            (path, pathItem) -> {
              pathItem
                  .readOperationsMap()
                  .forEach(
                      (httpMethod, operation) -> {
                        // Focus on GET operations that likely return collections
                        if (httpMethod.toString().equalsIgnoreCase("GET")
                            && isCollectionEndpoint(path, operation)) {

                          boolean hasPagination = checkPaginationSupport(operation);

                          if (!hasPagination) {
                            suggestions.add(
                                new ValidationSuggestion(
                                    String.format(
                                        "AI-Friendliness: %s %s appears to return a collection but"
                                            + " lacks pagination parameters. Add limit/offset or"
                                            + " cursor-based pagination to prevent AI agents from"
                                            + " inefficiently fetching all data.\n\n"
                                            + "WHY: AI agents have limited token/memory budgets and"
                                            + " request timeouts. Without pagination, agents must"
                                            + " fetch entire collections at once, which can cause"
                                            + " timeouts, memory exhaustion, or excessive costs."
                                            + " Pagination allows agents to retrieve data in"
                                            + " manageable chunks and stop when they have enough"
                                            + " information, dramatically improving performance and"
                                            + " reliability.",
                                        httpMethod, path),
                                    RULE_ID,
                                    "warning",
                                    "ai-friendliness",
                                    Map.of(
                                        "path",
                                        path,
                                        "method",
                                        httpMethod.toString(),
                                        "recommendation",
                                        "Add pagination parameters: limit, offset, or cursor",
                                        "example_params",
                                        List.of("limit", "offset", "page", "cursor", "next_token"),
                                        "why",
                                        "Prevents timeouts and memory issues when agents work with"
                                            + " large datasets"),
                                    true));
                          }
                        }
                      });
            });

    return suggestions;
  }

  /**
   * Determine if an endpoint likely returns a collection based on: - Path naming (plural, /items,
   * /list) - Operation summary/description - Response schema (array type)
   */
  private boolean isCollectionEndpoint(String path, Operation operation) {
    // Check path for plural or collection indicators
    String lowerPath = path.toLowerCase(Locale.ROOT);
    boolean pathIndicatesCollection = lowerPath.matches(".*(s|list|all|search|query)(/.*)?$");

    // Check operation summary/description
    String summary = operation.getSummary() != null ? operation.getSummary().toLowerCase(Locale.ROOT) : "";
    String description =
        operation.getDescription() != null ? operation.getDescription().toLowerCase(Locale.ROOT) : "";
    boolean descIndicatesCollection =
        summary.contains("list")
            || summary.contains("all")
            || description.contains("list")
            || description.contains("all")
            || summary.contains("search")
            || description.contains("search");

    // Check if success response is an array
    boolean responseIsArray = false;
    if (operation.getResponses() != null && operation.getResponses().get("200") != null) {
      var response = operation.getResponses().get("200");
      if (response.getContent() != null && response.getContent().get("application/json") != null) {
        var schema = response.getContent().get("application/json").getSchema();
        if (schema != null && "array".equals(schema.getType())) {
          responseIsArray = true;
        }
      }
    }

    return pathIndicatesCollection || descIndicatesCollection || responseIsArray;
  }

  /**
   * Check if operation has pagination parameters.
   */
  private boolean checkPaginationSupport(Operation operation) {
    if (operation.getParameters() == null || operation.getParameters().isEmpty()) {
      return false;
    }

    List<String> paginationParams =
        List.of(
            "limit",
            "offset",
            "page",
            "per_page",
            "pagesize",
            "cursor",
            "next",
            "next_token",
            "continuation_token");

    return operation.getParameters().stream()
        .map(Parameter::getName)
        .map(String::toLowerCase)
        .anyMatch(paginationParams::contains);
  }
}
