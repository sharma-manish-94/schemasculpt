package io.github.sharma_manish_94.schemasculpt_api.service.linter;

import io.github.sharma_manish_94.schemasculpt_api.dto.ValidationSuggestion;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.Operation;
import io.swagger.v3.oas.models.PathItem;
import io.swagger.v3.oas.models.media.Schema;
import io.swagger.v3.oas.models.parameters.Parameter;
import org.springframework.stereotype.Component;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

/**
 * Linter rule that checks for missing descriptions in operations, parameters, and schemas.
 * Following Spectral's operation-description rule and extending it to other components.
 */
@Component
public class MissingDescriptionRule implements LinterRule {

    @Override
    public List<ValidationSuggestion> lint(OpenAPI openApi) {
        List<ValidationSuggestion> suggestions = new ArrayList<>();

        // Check API level description
        if (openApi.getInfo() != null && (openApi.getInfo().getDescription() == null || openApi.getInfo().getDescription().trim().isEmpty())) {
            suggestions.add(new ValidationSuggestion(
                "API is missing a description in the 'info' section.",
                "add-api-description",
                "warning",
                "documentation",
                Map.of("location", "info.description"),
                true
            ));
        }

        // Check operation descriptions
        if (openApi.getPaths() != null) {
            suggestions.addAll(checkOperationDescriptions(openApi));
        }

        // Check schema descriptions
        if (openApi.getComponents() != null && openApi.getComponents().getSchemas() != null) {
            suggestions.addAll(checkSchemaDescriptions(openApi));
        }

        return suggestions;
    }

    private List<ValidationSuggestion> checkOperationDescriptions(OpenAPI openApi) {
        List<ValidationSuggestion> suggestions = new ArrayList<>();

        for (Map.Entry<String, PathItem> pathEntry : openApi.getPaths().entrySet()) {
            String path = pathEntry.getKey();
            PathItem pathItem = pathEntry.getValue();

            for (Map.Entry<PathItem.HttpMethod, Operation> opEntry : pathItem.readOperationsMap().entrySet()) {
                PathItem.HttpMethod method = opEntry.getKey();
                Operation operation = opEntry.getValue();

                // Check operation description
                if (operation.getDescription() == null || operation.getDescription().trim().isEmpty()) {
                    suggestions.add(new ValidationSuggestion(
                        String.format("Operation '%s %s' is missing a description.", method, path),
                        "add-operation-description",
                        "warning",
                        "documentation",
                        Map.of("path", path, "method", method.toString()),
                        true
                    ));
                }

                // Check parameter descriptions
                if (operation.getParameters() != null) {
                    for (Parameter parameter : operation.getParameters()) {
                        if (parameter.getDescription() == null || parameter.getDescription().trim().isEmpty()) {
                            suggestions.add(new ValidationSuggestion(
                                String.format("Parameter '%s' in operation '%s %s' is missing a description.",
                                    parameter.getName(), method, path),
                                "add-parameter-description",
                                "info",
                                "documentation",
                                Map.of("path", path, "method", method.toString(), "parameter", parameter.getName()),
                                true
                            ));
                        }
                    }
                }
            }
        }

        return suggestions;
    }

    private List<ValidationSuggestion> checkSchemaDescriptions(OpenAPI openApi) {
        List<ValidationSuggestion> suggestions = new ArrayList<>();

        for (Map.Entry<String, Schema> schemaEntry : openApi.getComponents().getSchemas().entrySet()) {
            String schemaName = schemaEntry.getKey();
            Schema schema = schemaEntry.getValue();

            if (schema.getDescription() == null || schema.getDescription().trim().isEmpty()) {
                suggestions.add(new ValidationSuggestion(
                    String.format("Schema '%s' is missing a description.", schemaName),
                    "add-schema-description",
                    "warning",
                    "documentation",
                    Map.of("schemaName", schemaName),
                    true
                ));
            }

            // Check properties descriptions for object schemas
            if (schema.getProperties() != null) {
                schema.getProperties().forEach((propertyName, property) -> {
                    Schema propertySchema = (Schema) property;
                    if (propertySchema.getDescription() == null || propertySchema.getDescription().trim().isEmpty()) {
                        suggestions.add(new ValidationSuggestion(
                            String.format("Property '%s' in schema '%s' is missing a description.",
                                propertyName, schemaName),
                            "add-property-description",
                            "info",
                            "documentation",
                            Map.of("schemaName", schemaName, "propertyName", propertyName),
                            true
                        ));
                    }
                });
            }
        }

        return suggestions;
    }
}