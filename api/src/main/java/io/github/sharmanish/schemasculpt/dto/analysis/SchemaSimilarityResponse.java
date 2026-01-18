package io.github.sharmanish.schemasculpt.dto.analysis;

import java.util.List;
import java.util.Set;

public record SchemaSimilarityResponse(List<SchemaCluster> clusters) {
  public record SchemaCluster(
      Set<String> schemaNames,
      double similarityScore, // e.g., 0.95 for 95% similarity
      String suggestion // "Consider merging these..."
      ) {}
}
