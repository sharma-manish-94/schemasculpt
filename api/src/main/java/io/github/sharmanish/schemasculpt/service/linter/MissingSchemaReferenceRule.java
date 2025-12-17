package io.github.sharmanish.schemasculpt.service.linter;

import io.github.sharmanish.schemasculpt.dto.ValidationSuggestion;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.Operation;
import io.swagger.v3.oas.models.PathItem;
import io.swagger.v3.oas.models.media.Content;
import io.swagger.v3.oas.models.media.MediaType;
import io.swagger.v3.oas.models.media.Schema;
import io.swagger.v3.oas.models.responses.ApiResponse;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import org.springframework.stereotype.Component;

/**
 * Linter rule that detects missing schema references in the OpenAPI specification. When a schema
 * reference like #/components/schemas/Employee is used but the schema doesn't exist in components,
 * this rule suggests creating it.
 */
@Component
public class MissingSchemaReferenceRule implements LinterRule {

  private static final Pattern SCHEMA_REF_PATTERN =
      Pattern.compile("#/components/schemas/([^/\\s]+)");

  @Override
  public List<ValidationSuggestion> lint(OpenAPI openApi) {
    List<ValidationSuggestion> suggestions = new ArrayList<>();

    // Get all existing schema names
    Set<String> existingSchemas = new HashSet<>();
    if (openApi.getComponents() != null && openApi.getComponents().getSchemas() != null) {
      existingSchemas.addAll(openApi.getComponents().getSchemas().keySet());
    }

    // Check all operations for schema references
    if (openApi.getPaths() != null) {
      for (Map.Entry<String, PathItem> pathEntry : openApi.getPaths().entrySet()) {
        String path = pathEntry.getKey();
        PathItem pathItem = pathEntry.getValue();

        for (Map.Entry<PathItem.HttpMethod, Operation> opEntry :
            pathItem.readOperationsMap().entrySet()) {
          PathItem.HttpMethod method = opEntry.getKey();
          Operation operation = opEntry.getValue();

          // Check request body for missing schemas
          if (operation.getRequestBody() != null) {
            suggestions.addAll(
                checkContentForMissingSchemas(
                    operation.getRequestBody().getContent(),
                    existingSchemas,
                    path,
                    method.toString(),
                    "requestBody"));
          }

          // Check response schemas
          if (operation.getResponses() != null) {
            for (Map.Entry<String, ApiResponse> responseEntry :
                operation.getResponses().entrySet()) {
              String responseCode = responseEntry.getKey();
              ApiResponse response = responseEntry.getValue();

              if (response.getContent() != null) {
                suggestions.addAll(
                    checkContentForMissingSchemas(
                        response.getContent(),
                        existingSchemas,
                        path,
                        method.toString(),
                        "response[" + responseCode + "]"));
              }
            }
          }
        }
      }
    }

    return suggestions;
  }

  private List<ValidationSuggestion> checkContentForMissingSchemas(
      Content content, Set<String> existingSchemas, String path, String method, String location) {
    List<ValidationSuggestion> suggestions = new ArrayList<>();

    if (content == null) {
      return suggestions;
    }

    for (Map.Entry<String, MediaType> mediaEntry : content.entrySet()) {
      String mediaTypeName = mediaEntry.getKey();
      MediaType mediaType = mediaEntry.getValue();

      if (mediaType.getSchema() != null) {
        suggestions.addAll(
            checkSchemaForMissingRefs(
                mediaType.getSchema(),
                existingSchemas,
                path,
                method,
                location + "[" + mediaTypeName + "]"));
      }
    }

    return suggestions;
  }

  private List<ValidationSuggestion> checkSchemaForMissingRefs(
      Schema<?> schema,
      Set<String> existingSchemas,
      String path,
      String method,
      String location) {
    List<ValidationSuggestion> suggestions = new ArrayList<>();

    if (schema == null) {
      return suggestions;
    }

    // Check if this is a reference
    if (schema.get$ref() != null) {
      String ref = schema.get$ref();
      Matcher matcher = SCHEMA_REF_PATTERN.matcher(ref);

      if (matcher.find()) {
        String schemaName = matcher.group(1);

        // Check if schema exists
        if (!existingSchemas.contains(schemaName)) {
          suggestions.add(
              new ValidationSuggestion(
                  String.format(
                      "Path '%s' (%s) references schema '%s' which doesn't exist in components.",
                      path, method.toUpperCase(Locale.ROOT), schemaName),
                  "create-missing-schema",
                  "error",
                  "schema",
                  Map.of("schemaName", schemaName, "path", path, "method", method),
                  true));
        }
      }
    }

    // Check properties for nested schemas
    if (schema.getProperties() != null) {
      for (Map.Entry<String, Schema> propEntry : schema.getProperties().entrySet()) {
        suggestions.addAll(
            checkSchemaForMissingRefs(
                propEntry.getValue(), existingSchemas, path, method, location));
      }
    }

    // Check array items
    if (schema.getItems() != null) {
      suggestions.addAll(
          checkSchemaForMissingRefs(schema.getItems(), existingSchemas, path, method, location));
    }

    return suggestions;
  }
}
