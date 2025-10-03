package io.github.sharma_manish_94.schemasculpt_api.service.linter;

import io.github.sharma_manish_94.schemasculpt_api.dto.ValidationSuggestion;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.Operation;
import io.swagger.v3.oas.models.PathItem;
import io.swagger.v3.oas.models.media.MediaType;
import io.swagger.v3.oas.models.media.Schema;
import io.swagger.v3.oas.models.responses.ApiResponse;
import org.springframework.stereotype.Component;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

/**
 * Linter rule that checks for missing examples in schemas and responses.
 * Examples greatly improve API documentation usability.
 */
@Component
public class ExampleRule implements LinterRule {

    @Override
    public List<ValidationSuggestion> lint(OpenAPI openApi) {
        List<ValidationSuggestion> suggestions = new ArrayList<>();

        // Check schema examples
        if (openApi.getComponents() != null && openApi.getComponents().getSchemas() != null) {
            suggestions.addAll(checkSchemaExamples(openApi));
        }

        // Check response examples
        if (openApi.getPaths() != null) {
            suggestions.addAll(checkResponseExamples(openApi));
        }

        return suggestions;
    }

    private List<ValidationSuggestion> checkSchemaExamples(OpenAPI openApi) {
        List<ValidationSuggestion> suggestions = new ArrayList<>();

        for (Map.Entry<String, Schema> schemaEntry : openApi.getComponents().getSchemas().entrySet()) {
            String schemaName = schemaEntry.getKey();
            Schema schema = schemaEntry.getValue();

            if (shouldHaveExample(schema) && !hasExample(schema)) {
                suggestions.add(new ValidationSuggestion(
                    String.format("Schema '%s' should include an example for better documentation.", schemaName),
                    "add-schema-example",
                    "info",
                    "documentation",
                    Map.of("schemaName", schemaName, "location", "components.schemas." + schemaName),
                    true
                ));
            }
        }

        return suggestions;
    }

    private List<ValidationSuggestion> checkResponseExamples(OpenAPI openApi) {
        List<ValidationSuggestion> suggestions = new ArrayList<>();

        for (Map.Entry<String, PathItem> pathEntry : openApi.getPaths().entrySet()) {
            String path = pathEntry.getKey();
            PathItem pathItem = pathEntry.getValue();

            for (Map.Entry<PathItem.HttpMethod, Operation> opEntry : pathItem.readOperationsMap().entrySet()) {
                PathItem.HttpMethod method = opEntry.getKey();
                Operation operation = opEntry.getValue();

                if (operation.getResponses() != null) {
                    for (Map.Entry<String, ApiResponse> responseEntry : operation.getResponses().entrySet()) {
                        String responseCode = responseEntry.getKey();
                        ApiResponse response = responseEntry.getValue();

                        // Check success responses for examples
                        if (isSuccessResponse(responseCode) && response.getContent() != null) {
                            for (Map.Entry<String, MediaType> contentEntry : response.getContent().entrySet()) {
                                String mediaType = contentEntry.getKey();
                                MediaType content = contentEntry.getValue();

                                if (shouldHaveResponseExample(mediaType, content) && !hasResponseExample(content)) {
                                    suggestions.add(new ValidationSuggestion(
                                        String.format("Response '%s' for operation '%s %s' should include an example.",
                                            responseCode, method, path),
                                        "add-response-example",
                                        "info",
                                        "documentation",
                                        Map.of("path", path, "method", method.toString(),
                                               "responseCode", responseCode, "mediaType", mediaType),
                                        true
                                    ));
                                }
                            }
                        }
                    }
                }
            }
        }

        return suggestions;
    }

    private boolean shouldHaveExample(Schema schema) {
        // Skip certain schema types that don't benefit from examples
        if (schema == null) return false;

        String type = schema.getType();
        if (type == null) return true; // Object schemas without explicit type

        // Examples are particularly useful for object and array schemas
        return "object".equals(type) || "array".equals(type) ||
               // Also useful for enums and complex string patterns
               (schema.getEnum() != null && !schema.getEnum().isEmpty()) ||
               ("string".equals(type) && (schema.getPattern() != null || schema.getFormat() != null));
    }

    private boolean hasExample(Schema schema) {
        return schema.getExample() != null ||
               // Check for examples in properties for object schemas
               (schema.getProperties() != null && hasPropertyExamples(schema));
    }

    private boolean hasPropertyExamples(Schema schema) {
        if (schema.getProperties() == null) return false;

        // If at least some properties have examples, consider it acceptable
        long propertiesWithExamples = schema.getProperties().values().stream()
            .mapToLong(property -> hasExample((Schema) property) ? 1 : 0)
            .sum();

        return propertiesWithExamples > 0;
    }

    private boolean shouldHaveResponseExample(String mediaType, MediaType content) {
        // Focus on JSON responses primarily, but also other structured formats
        return mediaType.contains("json") ||
               mediaType.contains("xml") ||
               mediaType.contains("yaml");
    }

    private boolean hasResponseExample(MediaType content) {
        return content.getExample() != null ||
               (content.getExamples() != null && !content.getExamples().isEmpty()) ||
               // Check if schema has examples
               (content.getSchema() != null && hasExample(content.getSchema()));
    }

    private boolean isSuccessResponse(String responseCode) {
        try {
            int code = Integer.parseInt(responseCode);
            return code >= 200 && code < 300;
        } catch (NumberFormatException e) {
            return false;
        }
    }
}