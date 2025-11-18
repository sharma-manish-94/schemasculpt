package io.github.sharma_manish_94.schemasculpt_api.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.swagger.v3.oas.models.Components;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.Operation;
import io.swagger.v3.oas.models.media.Schema;
import io.swagger.v3.oas.models.parameters.RequestBody;
import io.swagger.v3.parser.OpenAPIV3Parser;
import io.swagger.v3.parser.core.models.ParseOptions;
import io.swagger.v3.parser.core.models.SwaggerParseResult;
import java.util.*;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

@Slf4j
@Service
public class AnalysisService {

  private static final String COMPONENTS_SCHEMAS_PREFIX = "#/components/schemas/";
  private static final String OPERATION_PREFIX = "Operations: ";
  private static final String SCHEMA_PREFIX = "Schema: ";
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

    Map<String, Schema> allSchemas =
        Optional.ofNullable(openApi.getComponents())
            .map(Components::getSchemas)
            .orElse(Collections.emptyMap());
    if (allSchemas.isEmpty()) {
      return reverseGraph;
    }

    allSchemas.keySet().forEach(schemaName -> reverseGraph.put(schemaName, new HashSet<>()));

    if (Objects.nonNull(openApi.getPaths())) {
      openApi
          .getPaths()
          .forEach(
              (pathName, pathItem) -> {
                pathItem
                    .readOperationsMap()
                    .forEach(
                        (httpMethod, operation) -> {
                          String dependantName = OPERATION_PREFIX + httpMethod + " " + pathName;
                          findRefsInOperation(operation, dependantName, reverseGraph);
                        });
              });
    }

    allSchemas.forEach(
        (schemaName, schema) -> {
          String dependantName = SCHEMA_PREFIX + schemaName;
          findRefsInSchema(schema, dependantName, reverseGraph, new HashSet<>());
        });

    return reverseGraph;
  }

  /**
   * Scans an operation's request bodies and responses for schema references
   *
   * @param operation operation for which request and response schema is being scanned
   * @param dependentName The name of the item that contains this schema (e.g., "Operation: GET
   *     /users").
   * @param reverseGraph The graph to populate.
   */
  private void findRefsInOperation(
      Operation operation, String dependentName, Map<String, Set<String>> reverseGraph) {
    Optional.ofNullable(operation.getRequestBody())
        .map(RequestBody::getContent)
        .ifPresent(
            content ->
                content
                    .values()
                    .forEach(
                        mediaType ->
                            findRefsInSchema(
                                mediaType.getSchema(),
                                dependentName,
                                reverseGraph,
                                new HashSet<>())));
    Optional.ofNullable(operation.getResponses())
        .ifPresent(
            apiResponses ->
                apiResponses
                    .values()
                    .forEach(
                        apiResponse -> {
                          Optional.ofNullable(apiResponse.getContent())
                              .ifPresent(
                                  content ->
                                      content
                                          .values()
                                          .forEach(
                                              mediaType ->
                                                  findRefsInSchema(
                                                      mediaType.getSchema(),
                                                      dependentName,
                                                      reverseGraph,
                                                      new HashSet<>())));
                        }));
  }

  /**
   * Recursively finds all $ref links within a given Schema object and adds them to the graph.
   *
   * @param schema The schema object to scan.
   * @param dependentName The name of the item that contains this schema (e.g., "Operation: GET
   *     /users").
   * @param reverseGraph The graph to populate.
   * @param visited A set to track visited schemas and prevent infinite recursion in circular
   *     models.
   */
  private void findRefsInSchema(
      Schema<?> schema,
      String dependentName,
      Map<String, Set<String>> reverseGraph,
      Set<Schema<?>> visited) {
    if (schema == null || visited.contains(schema)) {
      return;
    }
    visited.add(schema);
    processDirectReferences(schema, dependentName, reverseGraph);
    processObjectProperties(schema, dependentName, reverseGraph, visited);
    processArrayItems(schema, dependentName, reverseGraph, visited);
    processCompositeSchemas(schema, dependentName, reverseGraph, visited);
    visited.remove(schema);
  }

  private void processCompositeSchemas(
      Schema<?> schema,
      String dependentName,
      Map<String, Set<String>> reverseGraph,
      Set<Schema<?>> visited) {
    if (schema.getAllOf() != null) {
      schema.getAllOf().forEach(s -> findRefsInSchema(s, dependentName, reverseGraph, visited));
    }
    if (schema.getAnyOf() != null) {
      schema.getAnyOf().forEach(s -> findRefsInSchema(s, dependentName, reverseGraph, visited));
    }
    if (schema.getOneOf() != null) {
      schema.getOneOf().forEach(s -> findRefsInSchema(s, dependentName, reverseGraph, visited));
    }
  }

  private void processArrayItems(
      Schema<?> schema,
      String dependentName,
      Map<String, Set<String>> reverseGraph,
      Set<Schema<?>> visited) {
    if (schema.getItems() != null) {
      findRefsInSchema(schema.getItems(), dependentName, reverseGraph, visited);
    }
  }

  private void processObjectProperties(
      Schema<?> schema,
      String dependentName,
      Map<String, Set<String>> reverseGraph,
      Set<Schema<?>> visited) {
    if (schema.getProperties() != null) {
      schema
          .getProperties()
          .values()
          .forEach(
              propertySchema ->
                  findRefsInSchema(propertySchema, dependentName, reverseGraph, visited));
    }
  }

  private void processDirectReferences(
      Schema<?> schema, String dependentName, Map<String, Set<String>> reverseGraph) {
    if (schema.get$ref() != null) {
      String refPath = schema.get$ref();
      if (refPath.startsWith(COMPONENTS_SCHEMAS_PREFIX)) {
        String schemaName = refPath.substring(COMPONENTS_SCHEMAS_PREFIX.length());
        reverseGraph.computeIfAbsent(schemaName, k -> new HashSet<>()).add(dependentName);
      }
    }
  }

  public Map<String, Integer> calculateAllDepths(String specText) {
    if (specText == null || specText.isEmpty()) {
      return Collections.emptyMap();
    }
    OpenAPI openApi = parseOpenApiSpec(specText);
    return calculateAllDepths(openApi);
  }

  public Map<String, Integer> calculateAllDepths(final OpenAPI openApi) {
    if (isOpenAPIInvalid(openApi)) {
      log.error("Parsed OpenAPI spec is null or has no paths");
      return Collections.emptyMap();
    }

    Map<String, Schema> allSchemas =
        Optional.ofNullable(openApi.getComponents())
            .map(Components::getSchemas)
            .orElse(Collections.emptyMap());
    return processAllOperations(openApi, allSchemas);
  }

  private boolean isOpenAPIInvalid(OpenAPI openApi) {
    return (openApi == null || openApi.getPaths() == null || openApi.getPaths().isEmpty());
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

  public int calculateNestingDepthForOperation(Operation operation, OpenAPI openApi) {
    if (operation == null || openApi == null || openApi.getComponents() == null) {
      return 0;
    }

    Map<String, Schema> allSchemas =
        Optional.ofNullable(openApi.getComponents())
            .map(Components::getSchemas)
            .orElse(Collections.emptyMap());

    JsonNode operationNode = objectMapper.valueToTree(operation);
    Map<String, Integer> memo = new HashMap<>();

    return calculateMaxDepth(operationNode, new HashSet<>(), allSchemas, memo);
  }
}
