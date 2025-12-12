package io.github.sharma_manish_94.schemasculpt_api.service.impl;

import io.github.sharma_manish_94.schemasculpt_api.dto.ValidationError;
import io.github.sharma_manish_94.schemasculpt_api.dto.ValidationResult;
import io.github.sharma_manish_94.schemasculpt_api.dto.ValidationSuggestion;
import io.github.sharma_manish_94.schemasculpt_api.service.SpecParsingService;
import io.github.sharma_manish_94.schemasculpt_api.service.ValidationService;
import io.github.sharma_manish_94.schemasculpt_api.service.linter.SpecificationLinter;
import io.swagger.v3.core.util.Json;
import io.swagger.v3.core.util.Yaml;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.parser.OpenAPIV3Parser;
import io.swagger.v3.parser.core.models.SwaggerParseResult;
import java.util.Collections;
import java.util.List;
import java.util.Objects;
import org.springframework.stereotype.Service;

@Service
public class ValidationServiceImpl implements ValidationService {

  private final SpecificationLinter specificationLinter;
  private final SpecParsingService specParsingService;

  public ValidationServiceImpl(
      final SpecificationLinter specificationLinter, final SpecParsingService specParsingService) {
    this.specificationLinter = specificationLinter;
    this.specParsingService = specParsingService;
  }

  @Override
  public ValidationResult analyze(final String specText) {
    if (specText == null || specText.trim().isEmpty()) {
      ValidationError error = new ValidationError("Specification content cannot be empty");
      return new ValidationResult(List.of(error), Collections.emptyList());
    }

    try {
      // Use Swagger parser with enhanced validation
      OpenAPIV3Parser parser = new OpenAPIV3Parser();
      SwaggerParseResult parseResult = parser.readContents(specText, null, null);

      if (parseResult == null) {
        ValidationError error =
            new ValidationError("Failed to parse the specification - invalid format");
        return new ValidationResult(List.of(error), Collections.emptyList());
      }

      // Extract validation errors from the parser
      List<ValidationError> errors =
          parseResult.getMessages().stream()
              .filter(Objects::nonNull)
              .map(message -> new ValidationError(cleanUpValidationMessage(message)))
              .toList();

      // Apply linting rules for suggestions if parsing was successful
      List<ValidationSuggestion> suggestions = Collections.emptyList();
      if (parseResult.getOpenAPI() != null) {
        suggestions = specificationLinter.lint(parseResult.getOpenAPI());
      } else if (errors.isEmpty()) {
        // If no OpenAPI object but also no errors, it might be a format issue
        errors =
            List.of(
                new ValidationError(
                    "Could not parse OpenAPI specification - check format and syntax"));
      }

      return new ValidationResult(errors, suggestions);

    } catch (Exception e) {
      ValidationError criticalError =
          new ValidationError(
              "Failed to parse the specification. Please check for syntax errors. Details: "
                  + e.getMessage());
      return new ValidationResult(List.of(criticalError), Collections.emptyList());
    }
  }

  /**
   * Cleans up validation messages from the Swagger parser to make them more user-friendly
   */
  private String cleanUpValidationMessage(String message) {
    if (message == null) {
      return "Unknown validation error";
    }

    // Remove technical prefixes that are not useful for end users
    String cleanedMessage = message;

    // Remove common technical prefixes
    if (cleanedMessage.startsWith("attribute ")) {
      cleanedMessage = cleanedMessage.substring(10);
    }

    // Capitalize first letter
    if (!cleanedMessage.isEmpty()) {
      cleanedMessage =
          Character.toUpperCase(cleanedMessage.charAt(0)) + cleanedMessage.substring(1);
    }

    // Ensure it ends with a period for consistency
    if (!cleanedMessage.endsWith(".")) {
      cleanedMessage += ".";
    }

    return cleanedMessage;
  }

  @Override
  public ValidationResult analyze(OpenAPI openApi) {
    if (openApi == null) {
      ValidationError error = new ValidationError("OpenAPI specification is null");
      return new ValidationResult(List.of(error), Collections.emptyList());
    }
    try {
      final String specContent = serializeOpenApiToString(openApi);
      return this.analyze(specContent);
    } catch (Exception e) {
      throw new RuntimeException(e);
    }
  }

  private String serializeOpenApiToString(OpenAPI openApi) throws Exception {
    try {
      return Json.pretty(openApi);
    } catch (Exception jsonException) {
      try {
        return Yaml.pretty(openApi);
      } catch (Exception yamlException) {
        throw new Exception(
            "Failed to serialize OpenAPI specification: " + jsonException.getMessage(),
            jsonException);
      }
    }
  }
}
