package io.github.sharmanish.schemasculpt.service.linter;

import io.github.sharmanish.schemasculpt.dto.ValidationSuggestion;
import io.swagger.v3.oas.models.OpenAPI;
import org.springframework.stereotype.Component;

import java.util.ArrayList;
import java.util.List;

@Component
public class AiAgentUtilityRule implements LinterRule {
	@Override
	public List<ValidationSuggestion> lint(OpenAPI openApi) {
		List<ValidationSuggestion> suggestions = new ArrayList<>();
		suggestions.addAll(checkEnumConsistency(openApi));
		suggestions.addAll(checkDescriptionQuality(openApi));
		suggestions.addAll(checkOperationIdClarity(openApi));
		return suggestions;
	}
}
