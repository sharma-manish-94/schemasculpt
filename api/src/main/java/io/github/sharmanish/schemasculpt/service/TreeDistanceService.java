package io.github.sharmanish.schemasculpt.service;

import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.media.Schema;
import java.util.Objects;
import java.util.function.ToDoubleBiFunction;
import java.util.function.ToDoubleFunction;
import org.jgrapht.Graph;
import org.jgrapht.alg.similarity.ZhangShashaTreeEditDistance;
import org.jgrapht.graph.DefaultDirectedGraph;
import org.jgrapht.graph.DefaultEdge;
import org.springframework.stereotype.Component;

@Component
public class TreeDistanceService {

  public record SpecNode(String path, String label, String type) {
    @Override
    public boolean equals(Object o) {
      if (this == o) return true;
      if (o == null || getClass() != o.getClass()) return false;
      SpecNode specNode = (SpecNode) o;
      return Objects.equals(path, specNode.path)
          && Objects.equals(label, specNode.label)
          && Objects.equals(type, specNode.type);
    }

    @Override
    public int hashCode() {
      return Objects.hash(path, label, type);
    }
  }

  // Helper record to carry both the Graph and its Root Node
  private record TreeData(Graph<SpecNode, DefaultEdge> graph, SpecNode root) {}

  public double calculateSpecDistance(OpenAPI spec1, OpenAPI spec2) {
    TreeData t1 = convertToTree(spec1);
    TreeData t2 = convertToTree(spec2);

    // Handle empty specs safely
    if (t1 == null && t2 == null) return 0.0;
    if (t1 == null) return t2.graph().vertexSet().size();
    if (t2 == null) return t1.graph().vertexSet().size();

    // Cost Functions
    ToDoubleFunction<SpecNode> insertCost = (node) -> 1.0;
    ToDoubleFunction<SpecNode> removeCost = (node) -> 1.0;
    ToDoubleBiFunction<SpecNode, SpecNode> changeCost =
        (n1, n2) -> {
          if (Objects.equals(n1.label(), n2.label()) && Objects.equals(n1.type(), n2.type())) {
            return 0.0;
          }
          return 1.0;
        };

    // Correct Constructor: Passing (Graph1, Root1, Graph2, Root2, Costs...)
    ZhangShashaTreeEditDistance<SpecNode, DefaultEdge> algorithm =
        new ZhangShashaTreeEditDistance<>(
            t1.graph(), t1.root(), t2.graph(), t2.root(), insertCost, removeCost, changeCost);

    return algorithm.getDistance();
  }

  private TreeData convertToTree(OpenAPI spec) {
    if (spec == null) return null;

    Graph<SpecNode, DefaultEdge> graph = new DefaultDirectedGraph<>(DefaultEdge.class);

    // 1. Create the Root Node explicitly
    SpecNode root = new SpecNode("root", "Root", "API");
    graph.addVertex(root);

    // 2. Populate the rest of the tree
    if (spec.getPaths() != null) {
      spec.getPaths()
          .forEach(
              (pathUrl, pathItem) -> {
                String pathId = "root.paths." + pathUrl;
                SpecNode pathNode = new SpecNode(pathId, pathUrl, "Path");
                graph.addVertex(pathNode);
                graph.addEdge(root, pathNode);

                pathItem
                    .readOperationsMap()
                    .forEach(
                        (method, operation) -> {
                          String opId = pathId + "." + method.name();
                          SpecNode opNode = new SpecNode(opId, method.name(), "Operation");
                          graph.addVertex(opNode);
                          graph.addEdge(pathNode, opNode);

                          if (operation.getParameters() != null) {
                            operation
                                .getParameters()
                                .forEach(
                                    param -> {
                                      String paramId = opId + ".param." + param.getName();
                                      SpecNode paramNode =
                                          new SpecNode(paramId, param.getName(), "Parameter");
                                      graph.addVertex(paramNode);
                                      graph.addEdge(opNode, paramNode);
                                    });
                          }

                          if (operation.getResponses() != null) {
                            operation
                                .getResponses()
                                .keySet()
                                .forEach(
                                    code -> {
                                      String resId = opId + ".res." + code;
                                      SpecNode resNode = new SpecNode(resId, code, "Response");
                                      graph.addVertex(resNode);
                                      graph.addEdge(opNode, resNode);
                                    });
                          }
                        });
              });
    }

    if (spec.getComponents() != null && spec.getComponents().getSchemas() != null) {
      String compId = "root.components";
      SpecNode componentsNode = new SpecNode(compId, "Components", "Container");
      graph.addVertex(componentsNode);
      graph.addEdge(root, componentsNode);

      spec.getComponents()
          .getSchemas()
          .forEach(
              (name, schema) -> {
                traverseSchema(graph, componentsNode, compId + "." + name, name, schema);
              });
    }

    // Return BOTH the graph and the root node we created
    return new TreeData(graph, root);
  }

  private void traverseSchema(
      Graph<SpecNode, DefaultEdge> graph,
      SpecNode parent,
      String currentPath,
      String name,
      Schema<?> schema) {
    String nodeType = schema.getType() == null ? "object" : schema.getType();
    SpecNode schemaNode = new SpecNode(currentPath, name, nodeType);
    graph.addVertex(schemaNode);
    graph.addEdge(parent, schemaNode);

    if (schema.getProperties() != null) {
      schema
          .getProperties()
          .forEach(
              (propName, propSchema) -> {
                traverseSchema(
                    graph, schemaNode, currentPath + "." + propName, propName, propSchema);
              });
    }

    if (schema.getItems() != null) {
      traverseSchema(graph, schemaNode, currentPath + ".items", "items", schema.getItems());
    }
  }
}
