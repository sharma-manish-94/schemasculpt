package io.github.sharmanish.schemasculpt.dto.analysis;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;

@JsonIgnoreProperties(ignoreUnknown = true)
public record IndexingResult(
    String repo_id,
    String repo_name,
    String status,
    String message,
    Integer chunks_indexed,
    Integer files_processed,
    String error
) {}
