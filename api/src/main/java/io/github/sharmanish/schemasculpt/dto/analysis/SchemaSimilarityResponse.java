package io.github.sharmanish.schemasculpt.dto.analysis;

import java.util.List;
import java.util.Set;

public record SchemaSimilarityResponse(List<SchemaCluster> clusters) {
  public record SchemaCluster(
      Set<String> schemas,
      double similarity_score, // matches Python field name
      List<String> shared_fields // matches Python field name
  ) {}
}
