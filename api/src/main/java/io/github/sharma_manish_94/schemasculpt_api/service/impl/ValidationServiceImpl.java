package io.github.sharma_manish_94.schemasculpt_api.service.impl;

import io.github.sharma_manish_94.schemasculpt_api.dto.ValidationError;
import io.github.sharma_manish_94.schemasculpt_api.dto.ValidationResult;
import io.github.sharma_manish_94.schemasculpt_api.dto.ValidationSuggestion;
import io.github.sharma_manish_94.schemasculpt_api.service.SpecParsingService;
import io.github.sharma_manish_94.schemasculpt_api.service.ValidationService;
import io.github.sharma_manish_94.schemasculpt_api.service.linter.SpecificationLinter;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.parser.core.models.SwaggerParseResult;
import org.springframework.stereotype.Service;

import java.util.Collections;
import java.util.List;
import java.util.Objects;

@Service
public class ValidationServiceImpl implements ValidationService {

    private final SpecificationLinter specificationLinter;
    private final SpecParsingService specParsingService;

    public ValidationServiceImpl(final SpecificationLinter specificationLinter,
                                 final SpecParsingService specParsingService) {
        this.specificationLinter = specificationLinter;
        this.specParsingService = specParsingService;
    }

    @Override
    public ValidationResult analyze(final String specText) {
        try {
            SwaggerParseResult parseResult = specParsingService.parse(specText);
            if (Objects.isNull(parseResult)) {
                ValidationError error = new ValidationError("Spec content is empty");
                return new ValidationResult(List.of(error), List.of());
            }
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

    @Override
    public ValidationResult analyze(OpenAPI openApi) {
        if (openApi == null) {
            return new ValidationResult(Collections.emptyList(), Collections.emptyList());
        }
        List<ValidationSuggestion> suggestions = specificationLinter.lint(openApi);
        return new ValidationResult(Collections.emptyList(), suggestions);
    }
}
