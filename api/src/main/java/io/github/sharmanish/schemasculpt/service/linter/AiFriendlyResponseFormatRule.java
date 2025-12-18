package io.github.sharmanish.schemasculpt.service.linter;

import io.github.sharmanish.schemasculpt.dto.ValidationSuggestion;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.Operation;
import io.swagger.v3.oas.models.media.Schema;
import io.swagger.v3.oas.models.responses.ApiResponse;
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
public class AiFriendlyResponseFormatRule implements LinterRule {

  private static boolean hasStandardName(String schemaName) {
    return schemaName.contains("error")
            || schemaName.contains("response")
            || schemaName.contains("result");
  }

  private static boolean isEnvelope(Map<String, Schema<?>> properties) {
    return properties.containsKey("success") || properties.containsKey("ok")
            && (properties.containsKey("data") || properties.containsKey("payload"));
  }

  private static boolean isProblemDetails(Map<String, Schema<?>> properties) {
    return properties.containsKey("type")
            && properties.containsKey("title")
            && properties.containsKey("status");
  }

  @Override
  public List<ValidationSuggestion> lint(OpenAPI openApi) {
    List<ValidationSuggestion> suggestions = new ArrayList<>();

    if (openApi.getPaths() == null) {
      return suggestions;
    }

    boolean hasGlobalStandardFormat = this.checkGlobalStandardFormats(openApi);
    if (!hasGlobalStandardFormat) {
      suggestions.add(this.createStandardWrapperSuggestion());
    }
    openApi.getPaths().forEach((path, pathItem) -> {
      pathItem.readOperationsMap().forEach(((httpMethod, operation) -> {
        lintOperation(path, httpMethod.toString(), operation, openApi, suggestions);
      }));
    });
    return suggestions;
  }

  private void lintOperation(String path, String method, Operation operation, OpenAPI openApi,
                             List<ValidationSuggestion> suggestions) {
    if (operation.getResponses() == null || operation.getResponses().isEmpty()) {
      return;
    }
    operation.getResponses().forEach((statusCode, response) -> {
      if (isErrorStatus(statusCode)) {
        this.validateErrorResponse(path, method, statusCode, response, openApi, suggestions);
      }
    });
  }

  private void validateErrorResponse(String path, String method, String statusCode, ApiResponse apiResponse,
                                     OpenAPI openAPI, List<ValidationSuggestion> suggestions) {
    if (apiResponse.getContent() == null
            || apiResponse.getContent().isEmpty()
            || !(apiResponse.getContent().containsKey("application/json"))) {
      return;
    }
    Schema schema = apiResponse.getContent().get("application/json").getSchema();
    if (null == schema) {
      return;
    }
    Schema resolvedSchema = this.resolveSchema(schema, openAPI);
    if (!isSchemaAiFriendly(resolvedSchema)) {
      suggestions.add(createErrorStructureSuggestion(path, method, statusCode));
    }
  }

  private ValidationSuggestion createErrorStructureSuggestion(String path, String method, String statusCode) {
    String message = String.format("""
            Operation [%s %s] returns a non-standard error response for status %s.
            
            WHY: When an AI agent receives an error, it attempts to 'reason' through a fix. \
            If the error body is just a plain string or missing a 'type' code, the agent cannot \
            determine if the error was a validation issue (retryable with better input) \
            or a system failure (non-retryable).""", method, path, statusCode);

    // Deep metadata helps automated tools or IDE plugins show specific fixes
    Map<String, Object> metadata = Map.of(
            "path", path,
            "method", method,
            "httpStatusCode", statusCode,
            "recommendation", "use-rfc7807-problem-details",
            "required_fields", List.of("type", "title", "detail"),
            "ai_action", "Enables 'Error-Correction-Loop' where the agent fixes parameters based on 'detail'."
    );

    return new ValidationSuggestion(
            message,
            "AI_UNSTRUCTURED_ERROR",
            "warning",
            "ai-operability",
            metadata,
            true
    );
  }

  private Schema resolveSchema(Schema schema, OpenAPI openAPI) {
    if (schema.get$ref() != null) {
      String ref = schema.get$ref();
      String schemaName = ref.substring(ref.lastIndexOf('/') + 1);
      if (openAPI.getComponents() != null
              && openAPI.getComponents().getSchemas() != null) {
        return openAPI.getComponents().getSchemas().get(schemaName);
      }
    }
    return schema;
  }

  private boolean isSchemaAiFriendly(Schema resolvedSchema) {
    if (null == resolvedSchema || null == resolvedSchema.getProperties()) {
      return false;
    }
    Map properties = resolvedSchema.getProperties();
    return properties.containsKey("error")
            || properties.containsKey("type")
            || properties.containsKey("title")
            || properties.containsKey("detail");
  }

  private boolean isErrorStatus(final String statusCode) {
    return statusCode.startsWith("4")
            || statusCode.startsWith("5")
            || statusCode.equalsIgnoreCase("default");
  }

private ValidationSuggestion createStandardWrapperSuggestion() {
	String message = """
			Missing standardized response wrapper or RFC 7807 Problem Details.
			
			WHY: AI agents (and MCP servers) perform best when they can use a 'Uniform Observation' pattern. \
			Without a standard wrapper, the agent must re-learn the success/failure indicators for every endpoint, \
			which increases token usage and the risk of hallucination.""";

	Map<String, Object> metadata = Map.of(
            "recommendation", "implement-standard-envelope",
            "severity_impact", "high_for_agents",
            "best_practices", List.of(
                  "RFC 7807 (Problem Details for HTTP APIs)",
                  "Envelope Pattern: { \"success\": boolean, \"data\": object, \"error\": object }"
            ),
            "remediation_example", Map.of(
                    "success", true,
                    "data", "{ ... }",
                    "trace_id", "unique-request-id-for-debugging"
            )
	);

    return new ValidationSuggestion(
          message,
          "AI_MISSING_STANDARD_WRAPPER",
          "info", // Or 'warning' depending on your strictness
          "ai-readability",
          metadata,
          true // fixable
  );
}

  private boolean checkGlobalStandardFormats(OpenAPI openApi) {
    if (openApi.getComponents() == null || openApi.getComponents().getSchemas() == null) {
      return false;
    }
    Map<String, Schema> schemas = openApi.getComponents().getSchemas();
    for (Map.Entry<String, Schema> entry : schemas.entrySet()) {
      String schemaName = entry.getKey().toLowerCase();
      Schema schema = entry.getValue();
      Map properties = schema.getProperties();
      if (null == properties) {
        continue;
      }
      // 1. Detect RFC 7807 (Problem Details) - The Gold Standard for AI Errors
      boolean isProblemDetails = isProblemDetails(properties);
      boolean isEnvelope = isEnvelope(properties);
      boolean hasStandardName = hasStandardName(schemaName);
      if ((isProblemDetails || isEnvelope) && hasStandardName) {
        return true;
      }
    }
    return false;
  }
}
