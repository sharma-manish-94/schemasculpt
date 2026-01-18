package io.github.sharmanish.schemasculpt.service.analyzer.dependency;

import io.github.sharmanish.schemasculpt.dto.analysis.BlastRadiusResponse;
import io.github.sharmanish.schemasculpt.service.analyzer.base.AbstractSchemaAnalyzer;
import io.swagger.v3.oas.models.OpenAPI;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Component;

/**
 * Analyzer that calculates the blast radius of a schema change.
 *
 * <p>Determines which operations would be affected by changes to a target schema using BFS
 * traversal of the reverse dependency graph.
 *
 * <p>Risk levels:
 *
 * <ul>
 *   <li>CRITICAL: >50% of operations affected
 *   <li>HIGH: 20-50% affected
 *   <li>MEDIUM: 1-20% affected
 *   <li>LOW: 0% affected
 * </ul>
 */
@Component
@RequiredArgsConstructor
public class BlastRadiusAnalyzer extends AbstractSchemaAnalyzer<BlastRadiusResponse> {

  private final ReverseDependencyGraphAnalyzer graphAnalyzer;

  /**
   * Not supported - use analyze(OpenAPI, String) instead.
   *
   * @throws UnsupportedOperationException always
   */
  @Override
  protected BlastRadiusResponse performAnalysis(OpenAPI openApi) {
    throw new UnsupportedOperationException(
        "Use analyze(OpenAPI openApi, String targetSchema) instead");
  }

  /**
   * Performs blast radius analysis for a specific target schema.
   *
   * @param openApi The OpenAPI specification
   * @param targetSchema The schema name to analyze
   * @return Blast radius analysis result with summary and detailed breakdown
   */
  public BlastRadiusResponse analyze(OpenAPI openApi, String targetSchema) {
    validateOpenApi(openApi);

    if (openApi.getComponents() == null
        || openApi.getComponents().getSchemas() == null
        || !openApi.getComponents().getSchemas().containsKey(targetSchema)) {
      return new BlastRadiusResponse(
          targetSchema,
          0,
          0,
          0.0,
          null,
          Set.of(),
          Set.of(),
          List.of("Schema '" + targetSchema + "' not found in components/schemas"));
    }

    // Build dependency graph
    Map<String, Set<String>> dependencyGraph = graphAnalyzer.analyze(openApi);

    // Calculate blast radius with detailed breakdown
    BlastRadiusResult result = calculateBlastRadius(targetSchema, dependencyGraph);

    // Calculate total operations
    int totalOps = 0;
    if (openApi.getPaths() != null) {
      for (var pathItem : openApi.getPaths().values()) {
        totalOps += pathItem.readOperationsMap().size();
      }
    }

    // Calculate percentage (avoid divide by zero)
    double percentage =
        totalOps == 0 ? 0.0 : ((double) result.affectedEndpoints.size() / totalOps) * 100;

    // Determine risk level based on percentage
    BlastRadiusResponse.RiskLevel risk = determineRiskLevel(percentage);

    return new BlastRadiusResponse(
        targetSchema,
        totalOps,
        result.affectedEndpoints.size(),
        Math.round(percentage * 100.0) / 100.0, // round to 2 decimals
        risk,
        result.directDependents,
        result.allAffectedSchemas,
        new ArrayList<>(result.affectedEndpoints));
  }

  /**
   * Determines risk level based on percentage of affected operations.
   *
   * @param percentage Percentage of operations affected
   * @return Risk level classification
   */
  private BlastRadiusResponse.RiskLevel determineRiskLevel(double percentage) {
    if (percentage > 50) {
      return BlastRadiusResponse.RiskLevel.CRITICAL;
    } else if (percentage > 20) {
      return BlastRadiusResponse.RiskLevel.HIGH;
    } else if (percentage > 0) {
      return BlastRadiusResponse.RiskLevel.MEDIUM;
    }
    return BlastRadiusResponse.RiskLevel.LOW;
  }

  /**
   * Calculates the total blast radius of a schema change using BFS.
   *
   * @param schemaName The name of the schema being changed
   * @param reverseGraph The reverse dependency graph
   * @return BlastRadiusResult containing endpoints, direct dependents, and all affected schemas
   */
  private BlastRadiusResult calculateBlastRadius(
      String schemaName, Map<String, Set<String>> reverseGraph) {
    Set<String> affectedEndpoints = new HashSet<>();
    Set<String> directDependents = new HashSet<>();
    Set<String> allAffectedSchemas = new HashSet<>();
    Set<String> visited = new HashSet<>();

    // BFS Queue
    List<String> queue = new ArrayList<>();
    queue.add(schemaName);
    visited.add(schemaName);

    boolean isFirstLevel = true;

    while (!queue.isEmpty()) {
      int levelSize = queue.size();

      for (int i = 0; i < levelSize; i++) {
        String current = queue.removeFirst();

        Set<String> dependents = reverseGraph.getOrDefault(current, Collections.emptySet());
        for (String dep : dependents) {
          if (dep.startsWith(OPERATION_PREFIX)) {
            // Leaf node: an endpoint/operation
            affectedEndpoints.add(dep);
          } else if (dep.startsWith(SCHEMA_PREFIX)) {
            // Intermediate node: another schema
            String nextSchema = dep.substring(SCHEMA_PREFIX.length());
            if (!visited.contains(nextSchema)) {
              visited.add(nextSchema);
              queue.add(nextSchema);
              allAffectedSchemas.add(nextSchema);

              // Track direct dependents (first level only)
              if (isFirstLevel) {
                directDependents.add(nextSchema);
              }
            }
          }
        }
      }
      isFirstLevel = false;
    }

    return new BlastRadiusResult(affectedEndpoints, directDependents, allAffectedSchemas);
  }

  /** Internal record to hold blast radius calculation results. */
  private record BlastRadiusResult(
      Set<String> affectedEndpoints,
      Set<String> directDependents,
      Set<String> allAffectedSchemas) {}
}
