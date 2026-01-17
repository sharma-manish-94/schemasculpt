package io.github.sharmanish.schemasculpt.dto.diff;

import jakarta.validation.constraints.NotBlank;

/**
 * Request for comparing two OpenAPI specifications.
 *
 * @param oldSpec The original (baseline) OpenAPI specification content (JSON or YAML string)
 * @param newSpec The new (proposed) OpenAPI specification content (JSON or YAML string)
 */
public record DiffRequest(
    @NotBlank(message = "Old specification must not be blank") String oldSpec,
    @NotBlank(message = "New specification must not be blank") String newSpec) {}
