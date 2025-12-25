package io.github.sharmanish.schemasculpt.service.analyzer.base;

import io.swagger.v3.oas.models.media.Schema;
import java.util.Map;
import java.util.Set;
import lombok.experimental.UtilityClass;

/**
 * Utility for recursive schema traversal in OpenAPI specifications.
 *
 * <p>Extracted from AnalysisService to be reused across analyzers. Handles circular references
 * through visited set tracking.
 */
@UtilityClass
public class SchemaTraversalUtil {

  private static final String COMPONENTS_SCHEMAS_PREFIX = "#/components/schemas/";

  /**
   * Recursively finds all $ref links within a given Schema object and adds them to the graph.
   *
   * @param schema The schema object to scan.
   * @param dependentName The name of the item that contains this schema (e.g., "Operations: GET
   *     /users").
   * @param reverseGraph The graph to populate.
   * @param visited A set to track visited schemas and prevent infinite recursion in circular
   *     models.
   */
  public static void findRefsInSchema(
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

  /**
   * Processes direct $ref references in the schema.
   *
   * @param schema The schema to process
   * @param dependentName The dependent name to add to the graph
   * @param reverseGraph The reverse dependency graph
   */
  private static void processDirectReferences(
      Schema<?> schema, String dependentName, Map<String, Set<String>> reverseGraph) {
    if (schema.get$ref() != null) {
      String refPath = schema.get$ref();
      if (refPath.startsWith(COMPONENTS_SCHEMAS_PREFIX)) {
        String schemaName = refPath.substring(COMPONENTS_SCHEMAS_PREFIX.length());
        reverseGraph.computeIfAbsent(schemaName, k -> new java.util.HashSet<>()).add(dependentName);
      }
    }
  }

  /**
   * Processes object properties recursively.
   *
   * @param schema The schema to process
   * @param dependentName The dependent name
   * @param reverseGraph The reverse dependency graph
   * @param visited Set of visited schemas
   */
  private static void processObjectProperties(
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

  /**
   * Processes array items recursively.
   *
   * @param schema The schema to process
   * @param dependentName The dependent name
   * @param reverseGraph The reverse dependency graph
   * @param visited Set of visited schemas
   */
  private static void processArrayItems(
      Schema<?> schema,
      String dependentName,
      Map<String, Set<String>> reverseGraph,
      Set<Schema<?>> visited) {
    if (schema.getItems() != null) {
      findRefsInSchema(schema.getItems(), dependentName, reverseGraph, visited);
    }
  }

  /**
   * Processes composite schemas (allOf, anyOf, oneOf) recursively.
   *
   * @param schema The schema to process
   * @param dependentName The dependent name
   * @param reverseGraph The reverse dependency graph
   * @param visited Set of visited schemas
   */
  private static void processCompositeSchemas(
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
}
