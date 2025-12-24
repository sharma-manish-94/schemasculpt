package io.github.sharmanish.schemasculpt.service;

import org.jgrapht.Graph;
import org.jgrapht.alg.cycle.TarjanSimpleCycles;
import org.jgrapht.alg.isomorphism.VF2GraphIsomorphismInspector;
import org.jgrapht.alg.scoring.BetweennessCentrality;
import org.jgrapht.alg.scoring.PageRank;
import org.jgrapht.graph.DefaultEdge;
import org.springframework.stereotype.Component;

import java.util.Comparator;
import java.util.List;
import java.util.Map;

@Component
public class NetworkAnalysisService {

  /**
   * PageRank: Which schemas are most critical?
   * If these break, the whole API breaks.
   */
  public Map<GraphBuilderService.ApiNode, Double> calculateImportance(
      Graph<GraphBuilderService.ApiNode, DefaultEdge> graph) {
    PageRank<GraphBuilderService.ApiNode, DefaultEdge> pageRank = new PageRank<>(graph,
        0.85);
    return pageRank.getScores();
  }

  /**
   * Betweenness: Which schemas connect disparate parts of the API?
   * Refactoring these helps split the monolith.
   */
  public Map<GraphBuilderService.ApiNode, Double> calculateBottlenecks(
      Graph<GraphBuilderService.ApiNode, DefaultEdge> graph) {
    BetweennessCentrality<GraphBuilderService.ApiNode, DefaultEdge> bc =
        new BetweennessCentrality<>(graph);
    return bc.getScores();
  }

  /**
   * CircularDependency: Prevent infinite loop in code generation
   * @param graph graph created in graph builder service
   * @return List of cycles
   */
  public List<List<GraphBuilderService.ApiNode>> findCircularDependencies(
      Graph<GraphBuilderService.ApiNode, DefaultEdge> graph) {
    TarjanSimpleCycles<GraphBuilderService.ApiNode, DefaultEdge> detector =
        new TarjanSimpleCycles<>(graph);
    return detector.findSimpleCycles();
  }

  /**
   * Checks for Node Compatibility
   * @param schemaGraphA first node to compare
   * @param schemaGraphB second node to compare
   * @return boolean stating whether the two schemas/nodes are identical
   */
  public boolean areStructurallyIdentical(
      Graph<GraphBuilderService.ApiNode, DefaultEdge> schemaGraphA,
      Graph<GraphBuilderService.ApiNode, DefaultEdge> schemaGraphB) {
    // Note: You need to pass sub-graphs representing just the two schemas to compare
    // Comparator that returns 0 if types match, non-zero otherwise
    Comparator<GraphBuilderService.ApiNode> nodeComparator = (n1, n2) -> {
      if (n1.type().equals(n2.type())) {
        return 0; // Match
      }
      return n1.type().compareTo(n2.type()); // No Match
    };

    // Comparator for edges (always match since DefaultEdge has no data)
    Comparator<DefaultEdge> edgeComparator = (e1, e2) -> 0;

    var inspector = new VF2GraphIsomorphismInspector<>(
        schemaGraphA,
        schemaGraphB,
        nodeComparator,
        edgeComparator
    );
    return inspector.isomorphismExists();
  }
}
