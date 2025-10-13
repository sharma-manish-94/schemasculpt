package io.github.sharma_manish_94.schemasculpt_api.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.swagger.v3.oas.models.Components;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.media.Schema;
import io.swagger.v3.parser.OpenAPIV3Parser;
import io.swagger.v3.parser.core.models.ParseOptions;
import io.swagger.v3.parser.core.models.SwaggerParseResult;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Iterator;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

@Slf4j
@Service
public class AnalysisService {

  private static final String COMPONENTS_SCHEMAS_PREFIX = "#/components/schemas/";
  private final ObjectMapper objectMapper;

  public AnalysisService(ObjectMapper objectMapper) {
    this.objectMapper = objectMapper;
  }

  /**
   * Builds a map where the key is a component name and the value is a set of all other
   * components/operations that depend on it.
   */
  public Map<String, Set<String>> buildReverseDependencyGraph(OpenAPI openApi) {
    Map<String, Set<String>> reverseGraph = new HashMap<>();
    if (openApi.getComponents() != null && openApi.getComponents().getSchemas() != null) {
      openApi
          .getComponents()
          .getSchemas()
          .keySet()
          .forEach(schemaName -> reverseGraph.put(schemaName, new HashSet<>()));
    }

    JsonNode specNode = objectMapper.valueToTree(openApi);

    // Scan all paths to find dependencies
    if (specNode.has("paths")) {
      specNode
          .get("paths")
          .properties()
          .forEach(
              pathEntry -> {
                String pathName = pathEntry.getKey();
                JsonNode pathItemNode = pathEntry.getValue();

                // Iterate over the methods (get, post, etc.)
                pathItemNode
                    .properties()
                    .forEach(
                        methodEntry -> {
                          String methodName = methodEntry.getKey().toUpperCase();
                          String dependentName = "Operation: " + methodName + " " + pathName;
                          findRefsInNode(methodEntry.getValue(), dependentName, reverseGraph);
                        });
              });
    }
    if (specNode.has("components") && specNode.get("components").has("schemas")) {
      specNode
          .get("components")
          .get("schemas")
          .fields()
          .forEachRemaining(
              componentEntry -> {
                String dependentName = "Schema: " + componentEntry.getKey();
                findRefsInNode(componentEntry.getValue(), dependentName, reverseGraph);
              });
    }
    return reverseGraph;
  }

  private void findRefsInNode(
      JsonNode node, String dependentName, Map<String, Set<String>> reverseGraph) {
    if (node == null) return;

    if (node.isObject()) {
      node.properties()
          .forEach(
              entry -> {
                if (entry.getKey().equals("$ref") && entry.getValue().isTextual()) {
                  String refPath = entry.getValue().asText();
                  if (refPath.startsWith("#/components/schemas/")) {
                    String schemaName = refPath.substring("#/components/schemas/".length());
                    reverseGraph
                        .computeIfAbsent(schemaName, k -> new HashSet<>())
                        .add(dependentName);
                  }
                } else {
                  findRefsInNode(entry.getValue(), dependentName, reverseGraph);
                }
              });
    } else if (node.isArray()) {
      node.forEach(element -> findRefsInNode(element, dependentName, reverseGraph));
    }
  }

  public Map<String, Integer> calculateAllDepths(String specText) {
    if (specText == null || specText.isEmpty()) {

      return Collections.emptyMap();
    }

    OpenAPI openApi = parseOpenApiSpec(specText);
    if (openApi == null || openApi.getPaths() == null || openApi.getPaths().isEmpty()) {
      log.error("Parsed OpenAPI spec is null or has no paths");
      return Collections.emptyMap();
    }

    Map<String, Schema> allSchemas =
        Optional.ofNullable(openApi.getComponents())
            .map(Components::getSchemas)
            .orElse(Collections.emptyMap());
    return processAllOperations(openApi, allSchemas);
  }

  private OpenAPI parseOpenApiSpec(String specText) {
    ParseOptions options = new ParseOptions();
    options.setResolve(false);

    SwaggerParseResult parseResult = new OpenAPIV3Parser().readContents(specText, null, options);

    if (parseResult.getMessages() != null && !parseResult.getMessages().isEmpty()) {
      log.warn("Warnings during OpenAPI parsing: " + parseResult.getMessages());
    }

    return parseResult.getOpenAPI();
  }

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
                          JsonNode operationNode = objectMapper.valueToTree(operation);
                          int maxDepth =
                              calculateMaxDepth(operationNode, new HashSet<>(), allSchemas, memo);
                          allDepths.put(operationKey, maxDepth);
                        }));

    return allDepths;
  }

  private int calculateMaxDepth(
      JsonNode node,
      Set<String> visited,
      Map<String, Schema> allSchemas,
      Map<String, Integer> memo) {
    if (node == null || !node.isContainerNode()) {
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
        if (schema == null) return 0;

        visited.add(schemaName);
        JsonNode schemaNode = objectMapper.valueToTree(schema);

        int nestedDepth = calculateMaxDepth(schemaNode, visited, allSchemas, memo);

        visited.remove(schemaName);

        memo.put(schemaName, nestedDepth);
        return 1 + nestedDepth;
      }
    }

    int maxDepth = 0;
    Iterator<JsonNode> elements = node.elements();
    while (elements.hasNext()) {
      int childDepth = calculateMaxDepth(elements.next(), new HashSet<>(visited), allSchemas, memo);
      maxDepth = Math.max(maxDepth, childDepth);
    }
    return maxDepth;
  }
}
