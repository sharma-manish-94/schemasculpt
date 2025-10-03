package io.github.sharma_manish_94.schemasculpt_api.service.linter;

import io.github.sharma_manish_94.schemasculpt_api.dto.ValidationSuggestion;
import io.swagger.v3.oas.models.OpenAPI;
import org.springframework.stereotype.Component;

import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.regex.Pattern;

@Component
public class SchemaNamingConventionRule implements LinterRule {
	
	private static final Pattern PASCAL_CASE_PATTERN = Pattern.compile("^[A-Z][a-zA-Z0-9]*$");
	
	@Override
	public List<ValidationSuggestion> lint(OpenAPI openApi) {
		if (openApi.getComponents() == null || openApi.getComponents().getSchemas() == null) {
			return Collections.emptyList();
		}
		
		return openApi.getComponents().getSchemas().keySet().stream()
				       .filter(schemaName -> !PASCAL_CASE_PATTERN.matcher(schemaName).matches())
				       .map(schemaName -> new ValidationSuggestion(
						       String.format("Schema name '%s' does not follow PascalCase convention.", schemaName),
						       "use-pascal-case",
						       "warning",
						       "general",
						       Map.of("schemaName", schemaName),
						       true
				       ))
				       .toList();
	}
}
