package io.github.sharmanish.schemasculpt.service.analyzer.complexity;

import io.github.sharmanish.schemasculpt.service.analyzer.base.AbstractSchemaAnalyzer;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.Operation;
import io.swagger.v3.oas.models.media.Schema;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Iterator;
import java.util.Map;
import java.util.Set;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;
import tools.jackson.databind.JsonNode;
import tools.jackson.databind.json.JsonMapper;

/**
 * Analyzer that calculates the maximum nesting depth of schemas in operations.
 *
 * <p>Nesting depth measures how deeply schemas are nested within an operation's request/response
 * structures. Higher nesting depths can indicate complex data models that may be harder to
 * understand and maintain.
 *
 * <p>Uses memoization to optimize repeated depth calculations for shared schemas.
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class NestingDepthAnalyzer extends AbstractSchemaAnalyzer<Map<String, Integer>> {

  private final JsonMapper jsonMapper;

  @Override
  protected Map<String, Integer> performAnalysis(OpenAPI openApi) {
    if (openApi.getPaths() == null || openApi.getPaths().isEmpty()) {
      log.error("OpenAPI spec has no paths");
      return Collections.emptyMap();
    }

    Map<String, Schema> allSchemas = getAllSchemas(openApi);
    return processAllOperations(openApi, allSchemas);
  }

  /**
   * Calculates nesting depth for a specific operation.
   *
   * @param operation The operation to analyze
   * @param openApi The OpenAPI specification
   * @return The maximum nesting depth
   */
  public int analyzeOperation(Operation operation, OpenAPI openApi) {
    if (operation == null || openApi == null || openApi.getComponents() == null) {
      return 0;
    }

    Map<String, Schema> allSchemas = getAllSchemas(openApi);
    JsonNode operationNode = jsonMapper.valueToTree(operation);
    Map<String, Integer> memo = new HashMap<>();

    return calculateMaxDepth(operationNode, new HashSet<>(), allSchemas, memo);
  }

  /**
   * Processes all operations in the specification.
   *
   * @param openApi The OpenAPI specification
   * @param allSchemas Map of all schemas
   * @return Map of operation key to maximum nesting depth
   */
  private Map<String, Integer> processAllOperations(
      OpenAPI openApi, Map<String, Schema> allSchemas) {
    Map<String, Integer> allDepths = new HashMap<>();
    Map<String, Integer> memo = new HashMap<>();

    openApi
        .getPaths()
        .forEach(
            (pathKey, pathItem) ->
                pathItem
                    .readOperationsMap()
                    .forEach(
                        (method, operation) -> {
                          String operationKey = method.toString() + " " + pathKey;
                          log.debug("Calculating depth for operation: " + operationKey);
                          JsonNode operationNode = jsonMapper.valueToTree(operation);
                          int maxDepth =
                              calculateMaxDepth(operationNode, new HashSet<>(), allSchemas, memo);
                          allDepths.put(operationKey, maxDepth);
                        }));

    return allDepths;
  }

  /**
   * Recursively calculates the maximum nesting depth of a JSON node.
   *
   * @param node The JSON node to analyze
   * @param visited Set of visited schema names to prevent cycles
   * @param allSchemas Map of all schemas
   * @param memo Memoization cache for computed depths
   * @return The maximum nesting depth
   */
  private int calculateMaxDepth(
      JsonNode node,
      Set<String> visited,
      Map<String, Schema> allSchemas,
      Map<String, Integer> memo) {
    if (node == null || !node.isContainer()) {
      return 0;
    }

    if (node.isObject() && node.has("$ref")) {
      String refPath = node.get("$ref").asText();
      if (refPath.startsWith(COMPONENTS_SCHEMAS_PREFIX)) {
        String schemaName = refPath.substring(COMPONENTS_SCHEMAS_PREFIX.length());

        if (memo.containsKey(schemaName)) {
          return 1 + memo.get(schemaName);
        }
        if (visited.contains(schemaName)) {
          return 0;
        }

        Schema schema = allSchemas.get(schemaName);
        if (schema == null) {
          return 0;
        }

        visited.add(schemaName);
        JsonNode schemaNode = jsonMapper.valueToTree(schema);

        int nestedDepth = calculateMaxDepth(schemaNode, visited, allSchemas, memo);

        visited.remove(schemaName);

        memo.put(schemaName, nestedDepth);
        return 1 + nestedDepth;
      }
    }

    int maxDepth = 0;
    Iterator<JsonNode> elements = node.iterator();
    while (elements.hasNext()) {
      int childDepth = calculateMaxDepth(elements.next(), new HashSet<>(visited), allSchemas, memo);
      maxDepth = Math.max(maxDepth, childDepth);
    }
    return maxDepth;
  }
}
