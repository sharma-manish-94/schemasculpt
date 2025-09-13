package io.github.sharma_manish_94.schemasculpt_api.dto;


import com.fasterxml.jackson.annotation.JsonInclude;
import java.util.Map;

@JsonInclude(JsonInclude.Include.NON_EMPTY)
public record ValidationSuggestion(
		String message,
		String ruleId,
		Map<String, Object> context
) {
	public ValidationSuggestion(String message) {
		this(message, null, Map.of());
	}
}
