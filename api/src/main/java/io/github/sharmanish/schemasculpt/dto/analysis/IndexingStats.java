package io.github.sharmanish.schemasculpt.dto.analysis;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import java.util.List;
import java.util.Map;

@JsonIgnoreProperties(ignoreUnknown = true)
public record IndexingStats(
    Integer total_chunks,
    List<String> repositories,
    Map<String, Integer> languages,
    Map<String, Integer> chunk_types
) {}
