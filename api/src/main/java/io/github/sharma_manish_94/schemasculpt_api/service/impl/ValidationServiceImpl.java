package io.github.sharma_manish_94.schemasculpt_api.service.impl;

import io.github.sharma_manish_94.schemasculpt_api.dto.ValidationError;
import io.github.sharma_manish_94.schemasculpt_api.dto.ValidationResult;
import io.github.sharma_manish_94.schemasculpt_api.dto.ValidationSuggestion;
import io.github.sharma_manish_94.schemasculpt_api.service.ValidationService;
import io.github.sharma_manish_94.schemasculpt_api.service.linter.SpecificationLinter;
import io.swagger.v3.parser.OpenAPIV3Parser;
import io.swagger.v3.parser.core.models.SwaggerParseResult;
import org.springframework.stereotype.Service;

import java.util.Collections;
import java.util.List;

@Service
public class ValidationServiceImpl implements ValidationService {
	
	private final SpecificationLinter specificationLinter;
	
	public ValidationServiceImpl(SpecificationLinter specificationLinter) {
		this.specificationLinter = specificationLinter;
	}
	
	@Override
	public ValidationResult analyze(final String specText) {
		try {
			SwaggerParseResult parseResult = new OpenAPIV3Parser().readContents(specText);
			final List<ValidationError> errors = parseResult.getMessages().stream().map(ValidationError::new)
					                                     .toList();
			List<ValidationSuggestion> suggestions = Collections.emptyList();
			if (parseResult.getOpenAPI() != null) {
				suggestions = specificationLinter.lint(parseResult.getOpenAPI());
			}
			return new ValidationResult(errors, suggestions);
		} catch (Exception e) {
			ValidationError criticalError =
					new ValidationError("Failed to parse the specification. Please check for syntax errors. Details: " + e.getMessage());
			return new ValidationResult(List.of(criticalError), Collections.emptyList());
		}
	}
}
