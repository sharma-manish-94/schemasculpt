package io.github.sharma_manish_94.schemasculpt_api.dto;

import java.util.List;

public record ValidationResult(
		List<ValidationError> errors,
		List<ValidationSuggestion> suggestions
) {
}
