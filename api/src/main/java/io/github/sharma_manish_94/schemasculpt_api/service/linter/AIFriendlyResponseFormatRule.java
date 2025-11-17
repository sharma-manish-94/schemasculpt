package io.github.sharma_manish_94.schemasculpt_api.service.linter;

import io.github.sharma_manish_94.schemasculpt_api.dto.ValidationSuggestion;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.media.Schema;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import org.springframework.stereotype.Component;

/**
 * Linter rule that checks for AI-friendly standardized response formats.
 *
 * <p>AI agents benefit from consistent response structures across all endpoints. This rule suggests
 * using a standard wrapper like: {success, data, error} or RFC 7807 Problem Details format for
 * errors.
 */
@Component
public class AIFriendlyResponseFormatRule implements LinterRule {

  private static final String RULE_ID = "ai-friendly-response-format";

  @Override
  public List<ValidationSuggestion> lint(OpenAPI openApi) {
    List<ValidationSuggestion> suggestions = new ArrayList<>();

    if (openApi.getPaths() == null) {
      return suggestions;
    }

    // Track if we find standardized response schemas
    boolean hasStandardWrapper = false;
    boolean hasProblemDetails = false;

    // Check components for standard response schemas
    if (openApi.getComponents() != null && openApi.getComponents().getSchemas() != null) {
      Map<String, Schema> schemas = openApi.getComponents().getSchemas();

      // Check for standard success wrapper (e.g., ApiResponse, StandardResponse)
      for (Map.Entry<String, Schema> entry : schemas.entrySet()) {
        String schemaName = entry.getKey().toLowerCase();
        Schema schema = entry.getValue();

        if (schema.getProperties() != null) {
          Map<String, Schema> props = schema.getProperties();

          // Check for success/data/error pattern
          if (props.containsKey("success")
              && props.containsKey("data")
              && props.containsKey("error")) {
            hasStandardWrapper = true;
          }

          // Check for RFC 7807 Problem Details
          if (props.containsKey("type")
              && props.containsKey("title")
              && props.containsKey("status")
              && props.containsKey("detail")) {
            hasProblemDetails = true;
          }
        }
      }
    }

    // If no standard response format detected, suggest adding one
    if (!hasStandardWrapper && !hasProblemDetails) {
      suggestions.add(
          new ValidationSuggestion(
              "Consider implementing a standardized response format for AI-friendliness. AI agents"
                  + " benefit from consistent response structures. Recommended: {\"success\":"
                  + " boolean, \"data\": object, \"error\": string} or RFC 7807 Problem Details for"
                  + " errors.\n\n"
                  + "WHY: AI agents rely on predictable response structures to parse data reliably."
                  + " Without a standard format, agents must implement custom parsing logic for"
                  + " each API, increasing complexity and error rates. Standardized wrappers enable"
                  + " agents to universally detect success/failure and extract data without"
                  + " API-specific code.",
              RULE_ID,
              "info",
              "ai-friendliness",
              Map.of(
                  "recommendation",
                  "standardized-response-wrapper",
                  "formats",
                  List.of(
                      "Success wrapper: {success, data, error}",
                      "RFC 7807: {type, title, status, detail, instance}"),
                  "why",
                  "Predictable response structures eliminate the need for custom parsing logic"
                      + " per API"),
              true));
    }

    // Check if error responses use standard format
    openApi
        .getPaths()
        .forEach(
            (path, pathItem) -> {
              pathItem
                  .readOperationsMap()
                  .forEach(
                      (httpMethod, operation) -> {
                        if (operation.getResponses() != null) {
                          operation
                              .getResponses()
                              .forEach(
                                  (statusCode, response) -> {
                                    // Check error responses (4xx, 5xx)
                                    if (statusCode.startsWith("4") || statusCode.startsWith("5")) {
                                      if (response.getContent() != null
                                          && response
                                              .getContent()
                                              .containsKey("application/json")) {

                                        var mediaType =
                                            response.getContent().get("application/json");
                                        if (mediaType.getSchema() != null
                                            && mediaType.getSchema().get$ref() == null) {

                                          // Check if error response has proper structure
                                          Schema errorSchema = mediaType.getSchema();
                                          if (errorSchema.getProperties() == null
                                              || (!errorSchema.getProperties().containsKey("error")
                                                  && !errorSchema
                                                      .getProperties()
                                                      .containsKey("type"))) {

                                            suggestions.add(
                                                new ValidationSuggestion(
                                                    String.format(
                                                        "Error response %s for %s %s should use a"
                                                            + " structured format (e.g., RFC 7807"
                                                            + " Problem Details) for better AI"
                                                            + " agent compatibility.\n\n"
                                                            + "WHY: When errors occur, AI agents"
                                                            + " need to understand what went wrong"
                                                            + " and whether the request can be"
                                                            + " retried. Structured error formats"
                                                            + " (RFC 7807) provide machine-readable"
                                                            + " error codes, types, and details"
                                                            + " that agents can programmatically"
                                                            + " handle, enabling automated error"
                                                            + " recovery and better user"
                                                            + " experience.",
                                                        statusCode, httpMethod, path),
                                                    RULE_ID,
                                                    "warning",
                                                    "ai-friendliness",
                                                    Map.of(
                                                        "path",
                                                        path,
                                                        "method",
                                                        httpMethod.toString(),
                                                        "statusCode",
                                                        statusCode,
                                                        "why",
                                                        "Structured errors enable automated error"
                                                            + " recovery and retry logic"),
                                                    true));
                                          }
                                        }
                                      }
                                    }
                                  });
                        }
                      });
            });

    return suggestions;
  }
}
