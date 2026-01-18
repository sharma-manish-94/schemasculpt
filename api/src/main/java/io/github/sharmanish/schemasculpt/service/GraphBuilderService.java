package io.github.sharmanish.schemasculpt.service;

import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.Operation;
import io.swagger.v3.oas.models.media.Schema;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import org.apache.commons.lang3.StringUtils;
import org.jgrapht.Graph;
import org.jgrapht.graph.DefaultDirectedGraph;
import org.jgrapht.graph.DefaultEdge;
import org.springframework.stereotype.Service;

@Service
public class GraphBuilderService {

  public static final String SCHEMA = "SCHEMA";
  public static final String ENDPOINT = "ENDPOINT";

  public Graph<ApiNode, DefaultEdge> buildDependencyGraph(OpenAPI openApi) {
    Graph<ApiNode, DefaultEdge> graph = new DefaultDirectedGraph<>(DefaultEdge.class);
    if (openApi.getComponents() != null && openApi.getComponents().getSchemas() != null) {
      openApi
          .getComponents()
          .getSchemas()
          .keySet()
          .forEach(name -> graph.addVertex(new ApiNode(name, SCHEMA)));
    }
    if (openApi.getComponents() != null && openApi.getComponents().getSchemas() != null) {
      createGraphOfSharedSchemas(openApi, graph);
    }
    updateGraphWithOperationDetails(openApi, graph);
    return graph;
  }

  private void updateGraphWithOperationDetails(OpenAPI openApi, Graph<ApiNode, DefaultEdge> graph) {
    if (openApi.getPaths() != null) {
      openApi
          .getPaths()
          .forEach(
              (path, pathItem) ->
                  pathItem
                      .readOperationsMap()
                      .forEach(
                          (method, operation) -> {
                            ApiNode operNode = new ApiNode(method + " " + path, ENDPOINT);
                            graph.addVertex(operNode);
                            updateGraphWithRequestBody(graph, operation, operNode);
                            updateGraphWithResponses(graph, operation, operNode);
                          }));
    }
  }

  private void updateGraphWithResponses(
      Graph<ApiNode, DefaultEdge> graph, Operation operation, ApiNode operNode) {
    if (operation.getResponses() != null) {
      operation
          .getResponses()
          .values()
          .forEach(
              response -> {
                if (response.getContent() != null) {
                  response
                      .getContent()
                      .values()
                      .forEach(
                          mediaType -> {
                            List<String> refs = findRefs(mediaType.getSchema());
                            refs.forEach(refName -> addEdgeSafely(graph, operNode, refName));
                          });
                }
              });
    }
  }

  private void updateGraphWithRequestBody(
      Graph<ApiNode, DefaultEdge> graph, Operation operation, ApiNode operNode) {
    if (operation.getRequestBody() != null && operation.getRequestBody().getContent() != null) {
      operation
          .getRequestBody()
          .getContent()
          .values()
          .forEach(
              mediaType -> {
                List<String> refs = findRefs(mediaType.getSchema());
                refs.forEach(refName -> addEdgeSafely(graph, operNode, refName));
              });
    }
  }

  private void createGraphOfSharedSchemas(OpenAPI openApi, Graph<ApiNode, DefaultEdge> graph) {
    openApi
        .getComponents()
        .getSchemas()
        .forEach(
            (name, schema) -> {
              ApiNode source = new ApiNode(name, SCHEMA);
              findRefs(schema)
                  .forEach(
                      refName -> {
                        ApiNode target = new ApiNode(refName, SCHEMA);
                        if (!graph.containsVertex(target)) {
                          graph.addVertex(target);
                        }
                        if (!graph.containsVertex(source)) {
                          graph.addVertex(source);
                        }
                        graph.addEdge(source, target);
                      });
            });
  }

  private void addEdgeSafely(
      Graph<ApiNode, DefaultEdge> graph, ApiNode source, String targetSchemaName) {
    ApiNode target = new ApiNode(targetSchemaName, SCHEMA);
    if (!graph.containsVertex(target)) {
      graph.addVertex(target);
    }
    if (!source.equals(target)) {
      graph.addEdge(source, target);
    }
  }

  private List<String> findRefs(Schema<?> schema) {
    if (schema == null) {
      return List.of();
    }
    Set<String> refs = new HashSet<>();
    collectRefsRecursive(schema, refs);
    return new ArrayList<>(refs);
  }

  private void collectRefsRecursive(Schema<?> schema, Set<String> refs) {
    if (schema == null) {
      return;
    }
    if (schema.get$ref() != null) {
      String refName = extractSchemaName(schema.get$ref());
      if (StringUtils.isNotEmpty(refName)) {
        refs.add(refName);
      }
    }
    if (schema.getProperties() != null) {
      schema.getProperties().values().forEach(prop -> collectRefsRecursive(prop, refs));
    }
    extraSchemaNamesFromComposition(schema, refs);
    if (schema.getAdditionalProperties() != null
        && schema.getAdditionalProperties() instanceof Schema<?> additionalProp) {
      collectRefsRecursive(additionalProp, refs);
    }
  }

  private void extraSchemaNamesFromComposition(Schema<?> schema, Set<String> refs) {
    if (schema.getAllOf() != null) {
      schema.getAllOf().forEach(s -> collectRefsRecursive(s, refs));
    }
    if (schema.getOneOf() != null) {
      schema.getOneOf().forEach(s -> collectRefsRecursive(s, refs));
    }
    if (schema.getAnyOf() != null) {
      schema.getAnyOf().forEach(s -> collectRefsRecursive(s, refs));
    }
  }

  private String extractSchemaName(String ref) {
    if (StringUtils.isBlank(ref)) {
      return null;
    }
    int lastSlashIndex = ref.lastIndexOf("/");
    if (lastSlashIndex != -1 && lastSlashIndex < ref.length() - 1) {
      return ref.substring(lastSlashIndex + 1);
    }
    return ref;
  }

  public record ApiNode(String id, String type) {
    @Override
    public String toString() {
      return id;
    }
  }
}
