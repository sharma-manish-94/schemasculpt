package io.github.sharma_manish_94.schemasculpt_api.dto.analysis;

import java.util.List;
import java.util.Set;

public record SchemaSimilarityResponse(
        List<SchemaCluster> clusters
) {
    public record SchemaCluster(
            Set<String> schemaNames,
            double similarityScore, // e.g., 0.95 for 95% similarity
            String suggestion // "Consider merging these..."
    ) {
    }
}