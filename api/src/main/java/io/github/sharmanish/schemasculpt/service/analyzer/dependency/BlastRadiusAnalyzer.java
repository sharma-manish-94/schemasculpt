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
 *   <li>CRITICAL: >50% of endpoints affected
 *   <li>HIGH: 20-50% affected
 *   <li>MEDIUM: 0-20% affected
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
   * @return Blast radius analysis result
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
          List.of("Schema '" + targetSchema + "' not found in components/schemas"));
    }

    // Build dependency graph
    Map<String, Set<String>> dependencyGraph = graphAnalyzer.analyze(openApi);

    // Calculate blast radius
    Set<String> affectedRaw = calculateBlastRadius(targetSchema, dependencyGraph);

    // Calculate metrics
    int totalOps = 0;
    if (openApi.getPaths() != null) {
      for (var pathItem : openApi.getPaths().values()) {
        totalOps += pathItem.readOperationsMap().size();
      }
    }

    // Avoid divide by zero
    double percentage = totalOps == 0 ? 0.0 : ((double) affectedRaw.size() / totalOps) * 100;

    // Determine risk level
    BlastRadiusResponse.RiskLevel risk = BlastRadiusResponse.RiskLevel.LOW;
    if (percentage > 50) {
      risk = BlastRadiusResponse.RiskLevel.CRITICAL;
    } else if (percentage > 20) {
      risk = BlastRadiusResponse.RiskLevel.MEDIUM;
    } else if (percentage > 0) {
      risk = BlastRadiusResponse.RiskLevel.MEDIUM;
    }

    return new BlastRadiusResponse(
        targetSchema,
        totalOps,
        affectedRaw.size(),
        Math.round(percentage * 100.0) / 100.0, // round to 2 decimals
        risk,
        new ArrayList<>(affectedRaw));
  }

  /**
   * Calculates the total blast radius of a schema change using BFS.
   *
   * @param schemaName The name of the schema being changed
   * @param reverseGraph The reverse dependency graph
   * @return Set of all operations that depend on this schema
   */
  private Set<String> calculateBlastRadius(
      String schemaName, Map<String, Set<String>> reverseGraph) {
    Set<String> affectedEndpoints = new HashSet<>();
    Set<String> visited = new HashSet<>();

    // BFS Queue
    List<String> queue = new ArrayList<>();
    queue.add(schemaName);
    visited.add(schemaName);

    while (!queue.isEmpty()) {
      String current = queue.removeFirst();

      Set<String> dependents = reverseGraph.getOrDefault(current, Collections.emptySet());
      for (String dep : dependents) {
        if (dep.startsWith(OPERATION_PREFIX)) {
          // We reached a leaf node (an Endpoint)
          affectedEndpoints.add(dep);
        } else if (dep.startsWith(SCHEMA_PREFIX)) {
          // We reached an intermediate node (another Schema)
          String nextSchema = dep.substring(SCHEMA_PREFIX.length());
          if (!visited.contains(nextSchema)) {
            visited.add(nextSchema);
            queue.add(nextSchema);
          }
        }
      }
    }
    return affectedEndpoints;
  }
}
