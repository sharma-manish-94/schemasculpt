package io.github.sharmanish.schemasculpt.dto.request;

import jakarta.validation.constraints.NotBlank;

/**
 * Request to suggest a code fix for a specific vulnerability.
 *
 * @param vulnerableCode The snippet of vulnerable code.
 * @param language The programming language of the code.
 * @param vulnerabilityType A description of the vulnerability (e.g., "BOLA", "SQL Injection").
 */
public record SuggestFixRequest(
    @NotBlank String vulnerableCode,
    @NotBlank String language,
    @NotBlank String vulnerabilityType) {}
