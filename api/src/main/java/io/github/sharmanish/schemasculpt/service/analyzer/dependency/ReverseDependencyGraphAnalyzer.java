package io.github.sharmanish.schemasculpt.service.analyzer.dependency;

import io.github.sharmanish.schemasculpt.service.analyzer.base.AbstractSchemaAnalyzer;
import io.github.sharmanish.schemasculpt.service.analyzer.base.SchemaTraversalUtil;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.Operation;
import io.swagger.v3.oas.models.media.Schema;
import io.swagger.v3.oas.models.parameters.RequestBody;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.springframework.stereotype.Component;

/**
 * Analyzer that builds a reverse dependency graph showing which operations and schemas depend on
 * each component schema.
 *
 * <p>The result is a map where:
 *
 * <ul>
 *   <li>Key: Component schema name (e.g., "User")
 *   <li>Value: Set of dependents (e.g., "Operations: GET /users", "Schema: UserList")
 * </ul>
 */
@Component
public class ReverseDependencyGraphAnalyzer
    extends AbstractSchemaAnalyzer<Map<String, Set<String>>> {

  @Override
  protected Map<String, Set<String>> performAnalysis(OpenAPI openApi) {
    Map<String, Set<String>> reverseGraph = new HashMap<>();

    Map<String, Schema> allSchemas = getAllSchemas(openApi);
    if (allSchemas.isEmpty()) {
      return reverseGraph;
    }

    // Initialize the graph with all schema names
    allSchemas.keySet().forEach(schemaName -> reverseGraph.put(schemaName, new HashSet<>()));

    // Scan all operations for dependencies
    if (Objects.nonNull(openApi.getPaths())) {
      openApi
          .getPaths()
          .forEach(
              (pathName, pathItem) -> {
                pathItem
                    .readOperationsMap()
                    .forEach(
                        (httpMethod, operation) -> {
                          String dependentName = OPERATION_PREFIX + httpMethod + " " + pathName;
                          findRefsInOperation(operation, dependentName, reverseGraph);
                        });
              });
    }

    // Scan all schemas for dependencies
    allSchemas.forEach(
        (schemaName, schema) -> {
          String dependentName = SCHEMA_PREFIX + schemaName;
          SchemaTraversalUtil.findRefsInSchema(
              schema, dependentName, reverseGraph, new HashSet<>());
        });

    return reverseGraph;
  }

  /**
   * Scans an operation's request bodies and responses for schema references.
   *
   * @param operation operation for which request and response schema is being scanned
   * @param dependentName The name of the item that contains this schema (e.g., "Operations: GET
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
                            SchemaTraversalUtil.findRefsInSchema(
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
                                                  SchemaTraversalUtil.findRefsInSchema(
                                                      mediaType.getSchema(),
                                                      dependentName,
                                                      reverseGraph,
                                                      new HashSet<>())));
                        }));
  }
}
