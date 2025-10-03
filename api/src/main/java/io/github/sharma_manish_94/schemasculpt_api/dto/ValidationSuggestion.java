package io.github.sharma_manish_94.schemasculpt_api.dto;


import com.fasterxml.jackson.annotation.JsonInclude;
import java.util.Map;

@JsonInclude(JsonInclude.Include.NON_EMPTY)
public record ValidationSuggestion(
		String message,
		String ruleId,
		String severity,
		String category,
		Map<String, Object> context,
		boolean explainable
) {
	public ValidationSuggestion(String message) {
		this(message, null, "info", "general", Map.of(), true);
	}

	public ValidationSuggestion(String message, String ruleId) {
		this(message, ruleId, "warning", "general", Map.of(), true);
	}

	public ValidationSuggestion(String message, String ruleId, String severity) {
		this(message, ruleId, severity, "general", Map.of(), true);
	}
}
