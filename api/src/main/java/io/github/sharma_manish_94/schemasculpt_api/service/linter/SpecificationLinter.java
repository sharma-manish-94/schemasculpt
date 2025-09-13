package io.github.sharma_manish_94.schemasculpt_api.service.linter;

import io.github.sharma_manish_94.schemasculpt_api.dto.ValidationSuggestion;
import io.swagger.v3.oas.models.OpenAPI;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class SpecificationLinter {
	private final List<LinterRule> rules;
	
	public SpecificationLinter(List<LinterRule> rules) {
		this.rules = rules;
	}
	
	public List<ValidationSuggestion> lint(OpenAPI openAPI) {
		return rules.stream().flatMap(linterRule -> linterRule.lint(openAPI).stream())
				       .toList();
	}
}
