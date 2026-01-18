package io.github.sharmanish.schemasculpt.service.analyzer.quality;

import io.github.sharmanish.schemasculpt.dto.analysis.SchemaSimilarityResponse;
import io.github.sharmanish.schemasculpt.service.analyzer.base.AbstractSchemaAnalyzer;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.media.Schema;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.springframework.stereotype.Component;

/**
 * Analyzer that identifies duplicate or similar schemas using Jaccard similarity.
 *
 * <p>Compares schemas based on their property names and types. Schemas with >80% similarity are
 * grouped into clusters, suggesting opportunities for consolidation or base schema creation.
 *
 * <p>Uses O(n²) comparison algorithm - may be slow for large specifications with many schemas.
 */
@Component
public class SchemaSimilarityAnalyzer extends AbstractSchemaAnalyzer<SchemaSimilarityResponse> {

  private static final double SIMILARITY_THRESHOLD = 0.80;

  @Override
  protected SchemaSimilarityResponse performAnalysis(OpenAPI openApi) {
    List<SchemaSimilarityResponse.SchemaCluster> clusters = new ArrayList<>();
    Map<String, Schema> schemas = getAllSchemas(openApi);

    if (schemas.isEmpty()) {
      return new SchemaSimilarityResponse(clusters);
    }

    List<String> schemaNames = new ArrayList<>(schemas.keySet());
    Set<String> processed = new HashSet<>();

    // Compare every schema against every other schema (O(n^2))
    for (int i = 0; i < schemaNames.size(); i++) {
      String nameA = schemaNames.get(i);
      if (processed.contains(nameA)) {
        continue;
      }

      Set<String> currentCluster = new HashSet<>();
      currentCluster.add(nameA);

      for (int j = i + 1; j < schemaNames.size(); j++) {
        String nameB = schemaNames.get(j);
        if (processed.contains(nameB)) {
          continue;
        }

        double similarity = calculateJaccardSimilarity(schemas.get(nameA), schemas.get(nameB));

        // Threshold: If 80% similar, group them
        if (similarity > SIMILARITY_THRESHOLD) {
          currentCluster.add(nameB);
          processed.add(nameB);
        }
      }

      if (currentCluster.size() > 1) {
        clusters.add(
            new SchemaSimilarityResponse.SchemaCluster(
                currentCluster,
                SIMILARITY_THRESHOLD,
                "These schemas share >80% structure. Consider creating a base" + " schema."));
      }
    }
    return new SchemaSimilarityResponse(clusters);
  }

  /**
   * Calculates Jaccard similarity between two schemas.
   *
   * @param schemaA First schema
   * @param schemaB Second schema
   * @return Similarity score between 0.0 and 1.0
   */
  private double calculateJaccardSimilarity(Schema schemaA, Schema schemaB) {
    // 1. Extract "features" (property names + types)
    Set<String> featuresA = extractSchemaFeatures(schemaA);
    Set<String> featuresB = extractSchemaFeatures(schemaB);

    if (featuresA.isEmpty() && featuresB.isEmpty()) {
      return 1.0; // Both empty = identical
    }
    if (featuresA.isEmpty() || featuresB.isEmpty()) {
      return 0.0;
    }

    // 2. Calculate Jaccard Index: (Intersection) / (Union)
    Set<String> intersection = new HashSet<>(featuresA);
    intersection.retainAll(featuresB);

    Set<String> union = new HashSet<>(featuresA);
    union.addAll(featuresB);

    return (double) intersection.size() / union.size();
  }

  /**
   * Extracts schema features as property name:type pairs.
   *
   * @param schema The schema to analyze
   * @return Set of features (e.g., "username:string", "age:integer")
   */
  private Set<String> extractSchemaFeatures(Schema schema) {
    Set<String> features = new HashSet<>();
    if (schema.getProperties() != null) {
      schema
          .getProperties()
          .forEach(
              (propName, propSchema) -> {
                String type =
                    propSchema instanceof Schema ? ((Schema) propSchema).getType() : "unknown";
                features.add(propName + ":" + type);
              });
    }
    return features;
  }
}
