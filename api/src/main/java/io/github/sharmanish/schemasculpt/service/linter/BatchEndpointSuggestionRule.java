package io.github.sharmanish.schemasculpt.service.linter;

import io.github.sharmanish.schemasculpt.dto.ValidationSuggestion;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.PathItem;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.regex.Pattern;
import java.util.stream.Collectors;
import org.springframework.stereotype.Component;

/**
 * Linter rule that suggests batch endpoints for AI-friendliness.
 *
 * <p>AI agents struggle with making many sequential API calls in loops. If an API has single-item
 * endpoints (GET /users/{id}, DELETE /users/{id}), suggest adding batch endpoints (POST
 * /users/batch-get, POST /users/batch-delete) to allow agents to perform operations on multiple
 * items efficiently.
 */
@Component
public class BatchEndpointSuggestionRule implements LinterRule {

  private static final String RULE_ID = "suggest-batch-endpoints";
  private static final Pattern PATH_PARAM_PATTERN = Pattern.compile("\\{([^}]+)\\}");

  @Override
  public List<ValidationSuggestion> lint(OpenAPI openApi) {
    List<ValidationSuggestion> suggestions = new ArrayList<>();

    if (openApi.getPaths() == null) {
      return suggestions;
    }

    // Group paths by resource (e.g., /users, /products)
    Map<String, List<PathInfo>> resourcePaths = groupPathsByResource(openApi);

    // For each resource, check if it has single-item operations but no batch operations
    resourcePaths.forEach(
        (resource, paths) -> {
          // Find single-item GET, DELETE, PUT, PATCH operations
          List<PathInfo> singleItemGets =
              paths.stream().filter(p -> p.hasPathParam && p.methods.contains("GET")).toList();

          List<PathInfo> singleItemDeletes =
              paths.stream().filter(p -> p.hasPathParam && p.methods.contains("DELETE")).toList();

          List<PathInfo> singleItemUpdates =
              paths.stream()
                  .filter(
                      p ->
                          p.hasPathParam
                              && (p.methods.contains("PUT") || p.methods.contains("PATCH")))
                  .toList();

          // Check if batch endpoints exist
          boolean hasBatchGet =
              paths.stream().anyMatch(p -> p.path.contains("batch") && p.methods.contains("POST"));

          boolean hasBatchDelete =
              paths.stream()
                  .anyMatch(
                      p -> p.path.contains("batch-delete") || p.path.contains("batch_delete"));

          boolean hasBatchUpdate =
              paths.stream()
                  .anyMatch(
                      p -> p.path.contains("batch-update") || p.path.contains("batch_update"));

          // Suggest batch GET if single-item GET exists but no batch
          if (!singleItemGets.isEmpty() && !hasBatchGet) {
            suggestions.add(
                new ValidationSuggestion(
                    String.format(
                        "AI-Friendliness: Consider adding a batch GET"
                            + " endpoint for /%s. AI agents can retrieve"
                            + " multiple items in one call instead of"
                            + " making sequential requests. Example: POST"
                            + " /%s/batch-get with body: {\"ids\":"
                            + " [...]}\n\n"
                            + "WHY: AI agents are inefficient at making"
                            + " many sequential API calls in loops. If an"
                            + " agent needs data for 100 items, making 100"
                            + " individual GET requests is slow, expensive"
                            + " (100x API costs), and unreliable (higher"
                            + " chance of failures). A batch endpoint"
                            + " reduces this to 1 request, dramatically"
                            + " improving speed, cost, and reliability.",
                        resource, resource),
                    RULE_ID,
                    "info",
                    "ai-friendliness",
                    Map.of(
                        "resource",
                        resource,
                        "operation",
                        "batch-get",
                        "benefit",
                        "Reduces chatty API calls from AI agents",
                        "why",
                        "One batch request replaces hundreds of sequential"
                            + " calls, improving speed 100x"),
                    true));
          }

          // Suggest batch DELETE if single-item DELETE exists but no batch
          if (!singleItemDeletes.isEmpty() && !hasBatchDelete) {
            suggestions.add(
                new ValidationSuggestion(
                    String.format(
                        "AI-Friendliness: Consider adding a batch DELETE"
                            + " endpoint for /%s. Example: POST"
                            + " /%s/batch-delete with body: {\"ids\":"
                            + " [...]}\n\n"
                            + "WHY: Cleanup operations often involve"
                            + " deleting many items. Forcing agents to make"
                            + " sequential DELETE calls is inefficient and"
                            + " error-prone. If any single request fails"
                            + " mid-loop, you end up with partial deletions"
                            + " and inconsistent state. Batch operations"
                            + " support atomic all-or-nothing deletions and"
                            + " dramatically reduce latency.",
                        resource, resource),
                    RULE_ID,
                    "info",
                    "ai-friendliness",
                    Map.of(
                        "resource",
                        resource,
                        "operation",
                        "batch-delete",
                        "benefit",
                        "Enables AI agents to delete multiple items" + " efficiently",
                        "why",
                        "Supports atomic operations and prevents partial"
                            + " failures in cleanup workflows"),
                    true));
          }

          // Suggest batch UPDATE if single-item UPDATE exists but no batch
          if (!singleItemUpdates.isEmpty() && !hasBatchUpdate) {
            suggestions.add(
                new ValidationSuggestion(
                    String.format(
                        "AI-Friendliness: Consider adding a batch UPDATE"
                            + " endpoint for /%s. Example: POST"
                            + " /%s/batch-update with body: {\"updates\":"
                            + " [{\"id\": ..., \"data\": ...}, ...]}\n\n"
                            + "WHY: Bulk update operations are common in"
                            + " automation workflows (e.g., updating status"
                            + " for multiple records, applying changes"
                            + " across a dataset). Sequential updates"
                            + " create race conditions, consistency issues,"
                            + " and performance bottlenecks. Batch updates"
                            + " allow agents to apply changes atomically"
                            + " and efficiently, ensuring data"
                            + " consistency.",
                        resource, resource),
                    RULE_ID,
                    "info",
                    "ai-friendliness",
                    Map.of(
                        "resource",
                        resource,
                        "operation",
                        "batch-update",
                        "benefit",
                        "Allows AI agents to update multiple items in one" + " request",
                        "why",
                        "Ensures consistency and prevents race conditions"
                            + " in bulk update workflows"),
                    true));
          }
        });

    return suggestions;
  }

  /** Group paths by their base resource (e.g., /users/{id} -> users). */
  private Map<String, List<PathInfo>> groupPathsByResource(OpenAPI openApi) {
    Map<String, List<PathInfo>> grouped = new HashMap<>();

    openApi
        .getPaths()
        .forEach(
            (path, pathItem) -> {
              String resource = extractResourceName(path);
              if (resource != null) {
                grouped
                    .computeIfAbsent(resource, k -> new ArrayList<>())
                    .add(new PathInfo(path, pathItem));
              }
            });

    return grouped;
  }

  /** Extract resource name from path (e.g., /users/{id} -> users). */
  private String extractResourceName(String path) {
    // Remove leading slash and split by /
    String[] parts = path.substring(1).split("/");

    // Return first non-parameterized segment
    for (String part : parts) {
      if (!part.contains("{")) {
        return part;
      }
    }

    return null;
  }

  /** Helper class to track path information. */
  private static class PathInfo {
    final String path;
    final boolean hasPathParam;
    final Set<String> methods;

    PathInfo(String path, PathItem pathItem) {
      this.path = path;
      this.hasPathParam = PATH_PARAM_PATTERN.matcher(path).find();
      this.methods =
          pathItem.readOperationsMap().keySet().stream()
              .map(Enum::toString)
              .collect(Collectors.toSet());
    }
  }
}
