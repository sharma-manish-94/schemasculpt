package io.github.sharma_manish_94.schemasculpt_api.service.linter;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.github.sharma_manish_94.schemasculpt_api.dto.ValidationSuggestion;
import io.swagger.v3.oas.models.OpenAPI;
import org.springframework.stereotype.Component;

import java.util.*;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

@Component
public class UnusedComponentRule implements LinterRule{
	
	private static final Pattern REF_PATTERN = Pattern.compile("\"\\$ref\":\\s*\"#/components/schemas/([^\"]+)\"");
	private final ObjectMapper jsonMapper = new ObjectMapper();
	
	@Override
	public List<ValidationSuggestion> lint(OpenAPI openApi) {
		if (openApi.getComponents() == null || openApi.getComponents().getSchemas() == null) {
			return Collections.emptyList();
		}
		
		Set<String> definedSchemas = openApi.getComponents().getSchemas().keySet();
		Set<String> referencedSchemas = new HashSet<>();
		
		try {
			String jsonString = jsonMapper.writeValueAsString(openApi);
			Matcher matcher = REF_PATTERN.matcher(jsonString);
			while (matcher.find()) {
				referencedSchemas.add(matcher.group(1));
			}
		} catch (JsonProcessingException e) {
			// If we can't process the spec, we can't find references.
			return Collections.emptyList();
		}
		
		return definedSchemas.stream()
				       .filter(defined -> !referencedSchemas.contains(defined))
				       .map(unused -> new ValidationSuggestion(
							   "Component schema '" + unused + "' is defined but never used.",
						       "remove-unused-component",
						       Map.of("componentName", unused)
						       ))
				       .toList();
	}
}
