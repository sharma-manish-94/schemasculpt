package io.github.sharma_manish_94.schemasculpt_api.service.impl;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.dataformat.yaml.YAMLFactory;
import io.github.sharma_manish_94.schemasculpt_api.dto.ValidationError;
import io.github.sharma_manish_94.schemasculpt_api.dto.ValidationResult;
import io.github.sharma_manish_94.schemasculpt_api.dto.ValidationSuggestion;
import io.github.sharma_manish_94.schemasculpt_api.service.ValidationService;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.parser.OpenAPIV3Parser;
import io.swagger.v3.parser.core.models.SwaggerParseResult;
import org.springframework.stereotype.Service;

import java.util.*;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

@Service
public class ValidationServiceImpl implements ValidationService {
	
	private static final Pattern REF_PATTERN = Pattern.compile("\"\\$ref\":\\s*\"#/components/schemas/([^\"]+)\"");
	private final ObjectMapper jsonMapper = new ObjectMapper();
	private final ObjectMapper yamlMapper = new ObjectMapper(new YAMLFactory());
	
	@Override
	public ValidationResult analyze(final String specText) {
		SwaggerParseResult parseResult = new OpenAPIV3Parser().readContents(specText);
		final List<ValidationError> errors = parseResult.getMessages().stream().map(ValidationError::new)
				                                     .toList();
		List<ValidationSuggestion> suggestions = new ArrayList<>();
		if (errors.isEmpty() && parseResult.getOpenAPI() != null) {
			suggestions.addAll(findUnusedComponents(parseResult.getOpenAPI()));
		}
		return new ValidationResult(errors, suggestions);
	}
	
	private List<ValidationSuggestion> findUnusedComponents(final OpenAPI openAPI) {
		if (openAPI.getComponents() == null ||
				    openAPI.getComponents().getSchemas() == null) {
			return Collections.emptyList();
		}
		final Set<String> definedSchemas = openAPI.getComponents().getSchemas().keySet();
		final Set<String> referencedSchemas = new HashSet<>();
		try {
			String jsonString = convertSpecToJson(openAPI);
			Matcher matcher = REF_PATTERN.matcher(jsonString);
			while (matcher.find()) {
				referencedSchemas.add(matcher.group(1));
			}
		} catch (JsonProcessingException e) {
			return Collections.emptyList();
		}
		return definedSchemas.stream()
				       .filter(defined -> !referencedSchemas.contains(defined))
				       .map(unused -> new ValidationSuggestion("Component schema '" + unused + "' is defined but never used."))
				       .toList();
	}
	
	private String convertSpecToJson(Object spec) throws JsonProcessingException {
		if(spec instanceof  OpenAPI) {
			return jsonMapper.writeValueAsString(spec);
		}
		return yamlMapper.writeValueAsString(spec);
	}
}
