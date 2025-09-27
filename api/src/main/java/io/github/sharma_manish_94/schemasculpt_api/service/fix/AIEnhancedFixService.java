package io.github.sharma_manish_94.schemasculpt_api.service.fix;

import io.github.sharma_manish_94.schemasculpt_api.dto.QuickFixRequest;
import io.github.sharma_manish_94.schemasculpt_api.service.SessionService;
import io.github.sharma_manish_94.schemasculpt_api.service.ai.EnhancedAIService;
import io.swagger.v3.core.util.Json;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.Operation;
import io.swagger.v3.oas.models.PathItem;
import io.swagger.v3.oas.models.info.Info;
import io.swagger.v3.oas.models.media.Schema;
import io.swagger.v3.oas.models.parameters.Parameter;
import io.swagger.v3.oas.models.responses.ApiResponse;
import io.swagger.v3.oas.models.tags.Tag;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Set;
import java.util.stream.Collectors;

@Service
public class AIEnhancedFixService {

    private final SessionService sessionService;
    private final EnhancedAIService aiService;

    public AIEnhancedFixService(SessionService sessionService, EnhancedAIService aiService) {
        this.sessionService = sessionService;
        this.aiService = aiService;
    }

    public OpenAPI applyAIFix(String sessionId, QuickFixRequest request) {
        OpenAPI openApi = sessionService.getSpecForSession(sessionId);
        if (openApi == null) {
            throw new IllegalArgumentException("Cannot apply AI fix to a null OpenAPI object.");
        }

        try {
            updateOpenAPIWithAI(request, openApi);
            sessionService.updateSessionSpec(sessionId, openApi);
            return openApi;
        } catch (Exception e) {
            throw new RuntimeException("AI-powered fix failed: " + e.getMessage(), e);
        }
    }

    private void updateOpenAPIWithAI(QuickFixRequest request, OpenAPI openApi) throws Exception {
        switch (request.ruleId()) {
            case "add-api-description":
                generateAPIDescription(openApi);
                break;
            case "add-operation-description":
                String path = (String) request.context().get("path");
                String method = (String) request.context().get("method");
                if (path != null && method != null) {
                    generateOperationDescription(openApi, path, method);
                }
                break;
            case "add-parameter-description":
                String paramPath = (String) request.context().get("path");
                String paramMethod = (String) request.context().get("method");
                String parameterName = (String) request.context().get("parameter");
                if (paramPath != null && paramMethod != null && parameterName != null) {
                    generateParameterDescription(openApi, paramPath, paramMethod, parameterName);
                }
                break;
            case "add-schema-description":
                String schemaName = (String) request.context().get("schemaName");
                if (schemaName != null) {
                    generateSchemaDescription(openApi, schemaName);
                }
                break;
            case "add-property-description":
                String propSchemaName = (String) request.context().get("schemaName");
                String propertyName = (String) request.context().get("propertyName");
                if (propSchemaName != null && propertyName != null) {
                    generatePropertyDescription(openApi, propSchemaName, propertyName);
                }
                break;
            case "add-schema-example":
                String exampleSchemaName = (String) request.context().get("schemaName");
                if (exampleSchemaName != null) {
                    generateSchemaExample(openApi, exampleSchemaName);
                }
                break;
            case "add-response-example":
                String responsePath = (String) request.context().get("path");
                String responseMethod = (String) request.context().get("method");
                String responseCode = (String) request.context().get("responseCode");
                String mediaType = (String) request.context().get("mediaType");
                if (responsePath != null && responseMethod != null && responseCode != null && mediaType != null) {
                    generateResponseExample(openApi, responsePath, responseMethod, responseCode, mediaType);
                }
                break;
            case "add-operation-summary":
                String summaryPath = (String) request.context().get("path");
                String summaryMethod = (String) request.context().get("method");
                if (summaryPath != null && summaryMethod != null) {
                    generateOperationSummary(openApi, summaryPath, summaryMethod);
                }
                break;
            case "add-operation-tags":
                String tagPath = (String) request.context().get("path");
                String tagMethod = (String) request.context().get("method");
                if (tagPath != null && tagMethod != null) {
                    generateOperationTags(openApi, tagPath, tagMethod);
                }
                break;
        }
    }

    private void generateAPIDescription(OpenAPI openApi) throws Exception {
        if (openApi.getInfo() == null) {
            openApi.setInfo(new Info());
        }

        String prompt = String.format(
            "Generate a concise, professional description for this OpenAPI specification. " +
            "Based on the API title '%s' and the available paths: %s. " +
            "Provide only the description text, no additional formatting.",
            openApi.getInfo().getTitle() != null ? openApi.getInfo().getTitle() : "API",
            openApi.getPaths() != null ? String.join(", ", openApi.getPaths().keySet()) : "No paths defined"
        );

        // Create an AI request for text processing
        String description = processTextUsingAI(prompt);
        openApi.getInfo().setDescription(description.trim());
    }

    private void generateOperationDescription(OpenAPI openApi, String path, String method) throws Exception {
        PathItem pathItem = openApi.getPaths().get(path);
        if (pathItem == null) return;

        Operation operation = pathItem.readOperationsMap().get(PathItem.HttpMethod.valueOf(method.toUpperCase()));
        if (operation == null) return;

        String prompt = String.format(
            "Generate a detailed description for this API operation: %s %s. " +
            "Consider the HTTP method and path to understand the operation's purpose. " +
            "Summary: %s. " +
            "Provide only the description text, no additional formatting.",
            method.toUpperCase(), path,
            operation.getSummary() != null ? operation.getSummary() : "No summary available"
        );

        // Create an AI request for text processing
        String description = processTextUsingAI(prompt);
        operation.setDescription(description.trim());
    }

    private void generateParameterDescription(OpenAPI openApi, String path, String method, String parameterName) throws Exception {
        PathItem pathItem = openApi.getPaths().get(path);
        if (pathItem == null) return;

        Operation operation = pathItem.readOperationsMap().get(PathItem.HttpMethod.valueOf(method.toUpperCase()));
        if (operation == null || operation.getParameters() == null) return;

        Parameter parameter = operation.getParameters().stream()
            .filter(p -> parameterName.equals(p.getName()))
            .findFirst()
            .orElse(null);

        if (parameter == null) return;

        String prompt = String.format(
            "Generate a description for this API parameter: '%s' in operation %s %s. " +
            "Parameter location: %s, Type: %s, Required: %s. " +
            "Provide only the description text, no additional formatting.",
            parameterName, method.toUpperCase(), path,
            parameter.getIn() != null ? parameter.getIn() : "unknown",
            parameter.getSchema() != null && parameter.getSchema().getType() != null ? parameter.getSchema().getType() : "unknown",
            parameter.getRequired() != null ? parameter.getRequired() : false
        );

        // Create an AI request for text processing
        String description = processTextUsingAI(prompt);
        parameter.setDescription(description.trim());
    }

    private void generateSchemaDescription(OpenAPI openApi, String schemaName) throws Exception {
        if (openApi.getComponents() == null || openApi.getComponents().getSchemas() == null) return;

        Schema schema = openApi.getComponents().getSchemas().get(schemaName);
        if (schema == null) return;

        String properties = "";
        if (schema.getProperties() != null) {
            properties = "Properties: " + String.join(", ", schema.getProperties().keySet());
        }

        String prompt = String.format(
            "Generate a description for this API schema: '%s'. " +
            "Schema type: %s. %s. " +
            "Provide only the description text, no additional formatting.",
            schemaName,
            schema.getType() != null ? schema.getType() : "object",
            properties
        );

        // Create an AI request for text processing
        String description = processTextUsingAI(prompt);
        schema.setDescription(description.trim());
    }

    private void generatePropertyDescription(OpenAPI openApi, String schemaName, String propertyName) throws Exception {
        if (openApi.getComponents() == null || openApi.getComponents().getSchemas() == null) return;

        Schema schema = openApi.getComponents().getSchemas().get(schemaName);
        if (schema == null || schema.getProperties() == null) return;

        Schema propertySchema = (Schema) schema.getProperties().get(propertyName);
        if (propertySchema == null) return;

        String prompt = String.format(
            "Generate a description for this property: '%s' in schema '%s'. " +
            "Property type: %s. " +
            "Provide only the description text, no additional formatting.",
            propertyName, schemaName,
            propertySchema.getType() != null ? propertySchema.getType() : "unknown"
        );

        // Create an AI request for text processing
        String description = processTextUsingAI(prompt);
        propertySchema.setDescription(description.trim());
    }

    private void generateSchemaExample(OpenAPI openApi, String schemaName) throws Exception {
        if (openApi.getComponents() == null || openApi.getComponents().getSchemas() == null) return;

        Schema schema = openApi.getComponents().getSchemas().get(schemaName);
        if (schema == null) return;

        String schemaJson = Json.pretty(schema);
        String prompt = String.format(
            "Generate a realistic example for this JSON schema: %s. " +
            "Provide only valid JSON data that conforms to the schema, no additional formatting or explanation.",
            schemaJson
        );

        String exampleJson = processTextUsingAI(prompt);
        try {
            // Parse and set the example
            Object example = Json.mapper().readValue(exampleJson, Object.class);
            schema.setExample(example);
        } catch (Exception e) {
            // If JSON parsing fails, set as string
            schema.setExample(exampleJson.trim());
        }
    }

    private void generateResponseExample(OpenAPI openApi, String path, String method, String responseCode, String mediaType) throws Exception {
        PathItem pathItem = openApi.getPaths().get(path);
        if (pathItem == null) return;

        Operation operation = pathItem.readOperationsMap().get(PathItem.HttpMethod.valueOf(method.toUpperCase()));
        if (operation == null || operation.getResponses() == null) return;

        ApiResponse response = operation.getResponses().get(responseCode);
        if (response == null || response.getContent() == null) return;

        io.swagger.v3.oas.models.media.MediaType content = response.getContent().get(mediaType);
        if (content == null) return;

        String prompt = String.format(
            "Generate a realistic example response for %s %s returning %s status. " +
            "Media type: %s. Operation description: %s. " +
            "Provide only valid JSON data, no additional formatting or explanation.",
            method.toUpperCase(), path, responseCode, mediaType,
            operation.getDescription() != null ? operation.getDescription() : "No description"
        );

        String exampleJson = processTextUsingAI(prompt);
        try {
            Object example = Json.mapper().readValue(exampleJson, Object.class);
            content.setExample(example);
        } catch (Exception e) {
            content.setExample(exampleJson.trim());
        }
    }

    private void generateOperationSummary(OpenAPI openApi, String path, String method) throws Exception {
        PathItem pathItem = openApi.getPaths().get(path);
        if (pathItem == null) return;

        Operation operation = pathItem.readOperationsMap().get(PathItem.HttpMethod.valueOf(method.toUpperCase()));
        if (operation == null) return;

        String prompt = String.format(
            "Generate a concise summary (max 50 characters) for this API operation: %s %s. " +
            "Consider the HTTP method and path structure. " +
            "Provide only the summary text, no additional formatting.",
            method.toUpperCase(), path
        );

        String summary = processTextUsingAI(prompt);
        operation.setSummary(summary.trim());
    }

    private void generateOperationTags(OpenAPI openApi, String path, String method) throws Exception {
        PathItem pathItem = openApi.getPaths().get(path);
        if (pathItem == null) return;

        Operation operation = pathItem.readOperationsMap().get(PathItem.HttpMethod.valueOf(method.toUpperCase()));
        if (operation == null) return;

        // Extract potential tag from path (first segment)
        String[] pathSegments = path.split("/");
        String suggestedTag = pathSegments.length > 1 ? pathSegments[1] : "general";

        String prompt = String.format(
            "Suggest 1-2 appropriate tags for this API operation: %s %s. " +
            "Consider the path structure and operation purpose. " +
            "Provide only comma-separated tag names, no additional formatting.",
            method.toUpperCase(), path
        );

        String tagsResponse = processTextUsingAI(prompt);
        String[] tags = tagsResponse.split(",");

        List<String> tagList = Arrays.stream(tags)
            .map(String::trim)
            .filter(tag -> !tag.isEmpty())
            .collect(Collectors.toList());

        if (!tagList.isEmpty()) {
            operation.setTags(tagList);

            // Add tags to OpenAPI tags list if not already present
            if (openApi.getTags() == null) {
                openApi.setTags(new ArrayList<>());
            }

            Set<String> existingTags = openApi.getTags().stream()
                .map(Tag::getName)
                .collect(Collectors.toSet());

            for (String tagName : tagList) {
                if (!existingTags.contains(tagName)) {
                    Tag newTag = new Tag();
                    newTag.setName(tagName);
                    openApi.getTags().add(newTag);
                }
            }
        }
    }
    /**
     * Helper method to process text using the AI service
     */
    private String processTextUsingAI(String prompt) throws Exception {
        try {
            // For now, return a placeholder response to avoid blocking compilation
            // In a real implementation, this would call the AI service asynchronously
            // and wait for the response
            return "AI-generated content based on: " + prompt.substring(0, Math.min(50, prompt.length()));
        } catch (Exception e) {
            // log.warn("AI processing failed, using fallback: {}", e.getMessage());
            return "Auto-generated content";
        }
    }
}
