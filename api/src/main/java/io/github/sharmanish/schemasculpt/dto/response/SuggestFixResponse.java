package io.github.sharmanish.schemasculpt.dto.response;

import jakarta.validation.constraints.NotBlank;

/**
 * Contains the AI-generated code fix.
 *
 * @param suggestedFix The complete, fixed code block suggested by the AI.
 */
public record SuggestFixResponse(@NotBlank String suggestedFix) {}
