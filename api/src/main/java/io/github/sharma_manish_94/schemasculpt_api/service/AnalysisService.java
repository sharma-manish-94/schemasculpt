package io.github.sharma_manish_94.schemasculpt_api.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.Operation;
import io.swagger.v3.oas.models.media.Schema;
import java.util.*;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

@Slf4j
@Service
public class AnalysisService {

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

  /** Calculates the maximum nesting depth for a given operation. */
  public int calculateMaxDepth(OpenAPI openApi, Operation operation) {
    JsonNode operationNode = objectMapper.valueToTree(operation);
    return calculateDepthRecursive(
        operationNode, new HashSet<>(), openApi.getComponents().getSchemas());
  }

  private int calculateDepthRecursive(
      JsonNode node, Set<String> visited, Map<String, Schema> allSchemas) {
    if (node == null || !node.isContainerNode()) {
      return 0; // Base case for non-objects/arrays
    }

    // Case 1: The node is a $ref object
    if (node.isObject() && node.has("$ref")) {
      String refPath = node.get("$ref").asText();
      if (refPath.startsWith("#/components/schemas/")) {
        String schemaName = refPath.substring("#/components/schemas/".length());

        if (visited.contains(schemaName)) {
          return 0; // Cycle detected
        }

        visited.add(schemaName); // Mark current path
        JsonNode nextNode = objectMapper.valueToTree(allSchemas.get(schemaName));
        int depth = 1 + calculateDepthRecursive(nextNode, visited, allSchemas); // Recurse
        visited.remove(schemaName); // Backtrack
        return depth;
      }
    }

    // Case 2: The node is a regular object or an array, so check its children
    int maxChildDepth = 0;
    if (node.isObject()) {
      // Correctly iterate through the fields of an object
      Iterator<Map.Entry<String, JsonNode>> fields = node.fields();
      while (fields.hasNext()) {
        Map.Entry<String, JsonNode> field = fields.next();
        maxChildDepth =
            Math.max(maxChildDepth, calculateDepthRecursive(field.getValue(), visited, allSchemas));
      }
    } else if (node.isArray()) {
      // Iterate through array elements
      for (JsonNode element : node) {
        maxChildDepth =
            Math.max(maxChildDepth, calculateDepthRecursive(element, visited, allSchemas));
      }
    }

    return maxChildDepth;
  }
}
