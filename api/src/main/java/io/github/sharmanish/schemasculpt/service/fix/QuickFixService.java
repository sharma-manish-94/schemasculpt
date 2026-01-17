package io.github.sharmanish.schemasculpt.service.fix;

import com.github.fge.jsonpatch.JsonPatchException;
import com.google.common.base.CaseFormat;
import io.github.sharmanish.schemasculpt.dto.QuickFixRequest;
import io.github.sharmanish.schemasculpt.dto.ai.PatchGenerationRequest;
import io.github.sharmanish.schemasculpt.dto.ai.PatchGenerationResponse;
import io.github.sharmanish.schemasculpt.exception.AIServiceException;
import io.github.sharmanish.schemasculpt.service.SessionService;
import io.github.sharmanish.schemasculpt.util.OpenApiEnumFixer;
import io.github.sharmanish.schemasculpt.util.VirtualThreads;
import io.swagger.v3.core.util.Json;
import io.swagger.v3.oas.models.Components;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.Operation;
import io.swagger.v3.oas.models.PathItem;
import io.swagger.v3.oas.models.media.Schema;
import java.util.Arrays;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Locale;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.concurrent.ExecutorService;
import java.util.regex.Pattern;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;
import tools.jackson.databind.json.JsonMapper;

@Service
public class QuickFixService {

  private static final Logger log = LoggerFactory.getLogger(QuickFixService.class);
  private static final Pattern PATH_PARAM_PATTERN = Pattern.compile("\\{([^}]+)}");

  // Rules that can be fixed automatically without AI
  private static final Set<String> AUTO_FIXABLE_RULES =
      new HashSet<>(
          Arrays.asList(
              "remove-unused-component",
              "generate-operation-id",
              "use-https",
              "use-https-for-production",
              "remove-trailing-slash",
              "fix-consecutive-slashes",
              "use-kebab-case",
              "replace-underscores-with-hyphens",
              "convert-camelcase-to-kebab",
              "add-success-response",
              "create-missing-schema",
              "add-missing-description"));

  private final SessionService sessionService;
  private final JsonPatchService jsonPatchService;
  private final JsonMapper jsonMapper;
  private final WebClient aiServiceClient;
  private final ExecutorService virtualThreadExecutor;

  public QuickFixService(
      SessionService sessionService,
      JsonPatchService jsonPatchService,
      JsonMapper jsonMapper,
      @Value("${ai.service.url:http://localhost:8000}") String aiServiceUrl,
      @Qualifier("virtualThreadExecutor") ExecutorService virtualThreadExecutor) {
    this.sessionService = Objects.requireNonNull(sessionService, "sessionService must not be null");
    this.jsonPatchService =
        Objects.requireNonNull(jsonPatchService, "jsonPatchService must not be null");
    this.jsonMapper = Objects.requireNonNull(jsonMapper, "jsonMapper must not be null");
    Objects.requireNonNull(aiServiceUrl, "aiServiceUrl must not be null");
    this.aiServiceClient = WebClient.builder().baseUrl(aiServiceUrl).build();
    this.virtualThreadExecutor =
        Objects.requireNonNull(virtualThreadExecutor, "virtualThreadExecutor must not be null");
  }

  public OpenAPI applyFix(String sessionId, QuickFixRequest request) {
    OpenAPI openApi = sessionService.getSpecForSession(sessionId);
    if (openApi == null) {
      throw new IllegalArgumentException("Cannot apply fix to a null OpenAPI object.");
    }

    // Check if this is an auto-fixable rule
    if (AUTO_FIXABLE_RULES.contains(request.ruleId())) {
      log.info("Applying auto-fix for rule: {}", request.ruleId());
      updateOpenAPI(request, openApi);
    } else {
      // Use AI service with JSON Patch approach
      log.info("Applying AI-powered fix for rule: {}", request.ruleId());
      openApi = applyAIFix(openApi, request);
    }

    sessionService.updateSessionSpec(sessionId, openApi);
    return openApi;
  }

  private void updateOpenAPI(QuickFixRequest request, OpenAPI openApi) {
    switch (request.ruleId()) {
      case "remove-unused-component":
        String componentName = (String) request.context().get("componentName");
        if (componentName != null
            && openApi.getComponents() != null
            && openApi.getComponents().getSchemas() != null) {
          openApi.getComponents().getSchemas().remove(componentName);
        }
        break;
      case "generate-operation-id":
        String path = (String) request.context().get("path");
        String method = (String) request.context().get("method");
        if (path != null && method != null) {
          generateOperationId(openApi, path, method);
        }
        break;
      case "use-https":
      case "use-https-for-production":
        String serverUrl = (String) request.context().get("serverUrl");
        Integer serverIndex = (Integer) request.context().get("serverIndex");
        if (serverUrl != null && serverIndex != null) {
          fixHttpsUrl(openApi, serverIndex, serverUrl);
        }
        break;
      case "remove-trailing-slash":
        String pathToFix = (String) request.context().get("path");
        if (pathToFix != null) {
          fixTrailingSlash(openApi, pathToFix);
        }
        break;
      case "fix-consecutive-slashes":
        String pathWithSlashes = (String) request.context().get("path");
        if (pathWithSlashes != null) {
          fixConsecutiveSlashes(openApi, pathWithSlashes);
        }
        break;
      case "use-kebab-case":
      case "replace-underscores-with-hyphens":
      case "convert-camelcase-to-kebab":
        String originalPath = (String) request.context().get("path");
        String segment = (String) request.context().get("segment");
        if (originalPath != null && segment != null) {
          fixPathNaming(openApi, originalPath, segment);
        }
        break;
      case "add-success-response":
        String opPath = (String) request.context().get("path");
        String opMethod = (String) request.context().get("method");
        if (opPath != null && opMethod != null) {
          addSuccessResponse(openApi, opPath, opMethod);
        }
        break;
      case "create-missing-schema":
        String schemaName = (String) request.context().get("schemaName");
        if (schemaName != null) {
          createMissingSchema(openApi, schemaName);
        }
        break;
      case "add-missing-description":
        String descPath = (String) request.context().get("path");
        String descMethod = (String) request.context().get("method");
        String responseCode = (String) request.context().get("responseCode");
        if (descPath != null && descMethod != null && responseCode != null) {
          addMissingDescription(openApi, descPath, descMethod, responseCode);
        }
        break;
    }
  }

  /**
   * Apply AI-powered fix using JSON Patch (RFC 6902). The AI service generates precise patch
   * operations instead of the full spec.
   */
  private OpenAPI applyAIFix(OpenAPI openApi, QuickFixRequest request) {
    try {
      // CRITICAL: Use Swagger's Json.pretty() instead of Spring's ObjectMapper
      // This ensures enums are serialized correctly as lowercase (oauth2, not OAUTH2)
      String specJson = Json.pretty(openApi);

      // Fix uppercase enums that Swagger parser stores in the model
      specJson = OpenApiEnumFixer.fixEnums(specJson);

      // Create request for AI service
      PatchGenerationRequest patchRequest =
          new PatchGenerationRequest(
              specJson,
              request.ruleId(),
              request.context(),
              "Generated fix for: " + request.ruleId());

      // Call AI service to generate JSON Patch
      PatchGenerationResponse patchResponse =
          VirtualThreads.executeBlocking(
              virtualThreadExecutor,
              () ->
                  aiServiceClient
                      .post()
                      .uri("/ai/patch/generate")
                      .bodyValue(patchRequest)
                      .retrieve()
                      .bodyToMono(PatchGenerationResponse.class)
                      .block());

      if (patchResponse == null || patchResponse.patches().isEmpty()) {
        log.warn("AI service returned no patch operations for rule: {}", request.ruleId());
        return openApi; // Return unchanged
      }

      log.info(
          "AI service generated {} patch operations with confidence: {}",
          patchResponse.patches().size(),
          patchResponse.confidence());

      // Apply the JSON Patch operations
      OpenAPI patchedSpec = jsonPatchService.applyPatch(openApi, patchResponse.patches());

      log.info(
          "Successfully applied AI-generated patch. Explanation: {}", patchResponse.explanation());
      return patchedSpec;

    } catch (JsonPatchException e) {
      log.error("Failed to apply AI-generated patch: {}", e.getMessage());
      throw new AIServiceException("AI fix failed: " + e.getMessage(), e);
    } catch (Exception e) {
      log.error("AI service call failed: {}", e.getMessage());
      throw new AIServiceException("AI service error: " + e.getMessage(), e);
    }
  }

  private void generateOperationId(OpenAPI openApi, String path, String method) {
    PathItem pathItem = openApi.getPaths().get(path);
    if (pathItem == null) {
      return;
    }

    Operation operation =
        pathItem
            .readOperationsMap()
            .get(PathItem.HttpMethod.valueOf(method.toUpperCase(Locale.ROOT)));
    if (operation == null) {
      return;
    }

    // Build the new operationId (e.g., "getUsersById")
    String generatedId = buildIdFromPath(method.toLowerCase(Locale.ROOT), path);
    operation.setOperationId(generatedId);
  }

  private void fixHttpsUrl(OpenAPI openApi, int serverIndex, String serverUrl) {
    if (openApi.getServers() != null && serverIndex < openApi.getServers().size()) {
      String httpsUrl = serverUrl.replaceFirst("^http://", "https://");
      openApi.getServers().get(serverIndex).setUrl(httpsUrl);
    }
  }

  private void fixTrailingSlash(OpenAPI openApi, String path) {
    if (openApi.getPaths() != null && openApi.getPaths().containsKey(path)) {
      String fixedPath = path.replaceAll("/+$", "");
      if (fixedPath.isEmpty()) {
        fixedPath = "/";
      }
      PathItem pathItem = openApi.getPaths().remove(path);
      openApi.getPaths().put(fixedPath, pathItem);
    }
  }

  private void fixConsecutiveSlashes(OpenAPI openApi, String path) {
    if (openApi.getPaths() != null && openApi.getPaths().containsKey(path)) {
      String fixedPath = path.replaceAll("/+", "/");
      PathItem pathItem = openApi.getPaths().remove(path);
      openApi.getPaths().put(fixedPath, pathItem);
    }
  }

  private void fixPathNaming(OpenAPI openApi, String originalPath, String segment) {
    if (openApi.getPaths() != null && openApi.getPaths().containsKey(originalPath)) {
      // Convert segment to kebab-case
      String fixedSegment =
          segment
              .replaceAll("([a-z])([A-Z])", "$1-$2") // Convert camelCase to kebab-case first
              .replaceAll("_", "-") // Replace underscores with hyphens
              .toLowerCase(Locale.ROOT);

      String fixedPath = originalPath.replace(segment, fixedSegment);
      PathItem pathItem = openApi.getPaths().remove(originalPath);
      openApi.getPaths().put(fixedPath, pathItem);
    }
  }

  private void addSuccessResponse(OpenAPI openApi, String path, String method) {
    PathItem pathItem = openApi.getPaths().get(path);
    if (pathItem == null) {
      return;
    }

    Operation operation =
        pathItem
            .readOperationsMap()
            .get(PathItem.HttpMethod.valueOf(method.toUpperCase(Locale.ROOT)));
    if (operation == null) {
      return;
    }

    if (operation.getResponses() == null) {
      operation.responses(new io.swagger.v3.oas.models.responses.ApiResponses());
    }

    // Add a default 200 response if no success response exists
    boolean hasSuccessResponse =
        operation.getResponses().keySet().stream()
            .anyMatch(
                code -> {
                  try {
                    int statusCode = Integer.parseInt(code);
                    return statusCode >= 200 && statusCode < 400;
                  } catch (NumberFormatException e) {
                    return false;
                  }
                });

    if (!hasSuccessResponse) {
      io.swagger.v3.oas.models.responses.ApiResponse successResponse =
          new io.swagger.v3.oas.models.responses.ApiResponse();
      successResponse.setDescription("Successful operation");
      operation.getResponses().put("200", successResponse);
    }
  }

  /**
   * Create a missing schema component with basic properties. Generates a stub schema that can be
   * filled in later.
   */
  private void createMissingSchema(OpenAPI openApi, String schemaName) {
    // Ensure components section exists
    if (openApi.getComponents() == null) {
      openApi.setComponents(new Components());
    }

    // Ensure schemas map exists
    if (openApi.getComponents().getSchemas() == null) {
      openApi.getComponents().setSchemas(new HashMap<>());
    }

    // Don't overwrite existing schemas
    if (openApi.getComponents().getSchemas().containsKey(schemaName)) {
      log.info("Schema {} already exists, skipping creation", schemaName);
      return;
    }

    // Create a basic object schema with placeholder properties
    Schema<?> newSchema = new Schema<>();
    newSchema.setType("object");
    newSchema.setDescription(
        "Auto-generated schema for " + schemaName + ". Please update with actual properties.");

    // Add a sample id property as a hint
    Map<String, Schema> properties = new HashMap<>();
    Schema<?> idProperty = new Schema<>();
    idProperty.setType("string");
    idProperty.setDescription("Unique identifier");
    properties.put("id", idProperty);

    newSchema.setProperties(properties);

    // Add the schema to components
    openApi.getComponents().getSchemas().put(schemaName, newSchema);

    log.info("Created stub schema for: {}", schemaName);
  }

  /**
   * Add a missing description to a response. Provides sensible defaults based on HTTP status code.
   */
  private void addMissingDescription(
      OpenAPI openApi, String path, String method, String responseCode) {
    PathItem pathItem = openApi.getPaths().get(path);
    if (pathItem == null) {
      return;
    }

    Operation operation =
        pathItem
            .readOperationsMap()
            .get(PathItem.HttpMethod.valueOf(method.toUpperCase(Locale.ROOT)));
    if (operation == null || operation.getResponses() == null) {
      return;
    }

    io.swagger.v3.oas.models.responses.ApiResponse response =
        operation.getResponses().get(responseCode);
    if (response == null) {
      return;
    }

    // Only add description if missing
    if (response.getDescription() == null || response.getDescription().trim().isEmpty()) {
      String description = getDefaultDescription(responseCode, method);
      response.setDescription(description);
      log.info(
          "Added description for {} {} response {}: {}",
          method.toUpperCase(Locale.ROOT),
          path,
          responseCode,
          description);
    }
  }

  private String buildIdFromPath(String method, String path) {
    String pathWithoutParams =
        PATH_PARAM_PATTERN
            .matcher(path)
            .replaceAll(
                match -> "By " + CaseFormat.LOWER_CAMEL.to(CaseFormat.UPPER_CAMEL, match.group(1)));

    String cleanPath = pathWithoutParams.replaceAll("[^a-zA-Z0-9 ]", " ").trim();

    return method.toLowerCase(Locale.ROOT)
        + CaseFormat.LOWER_HYPHEN.to(CaseFormat.UPPER_CAMEL, cleanPath.replace(" ", "-"));
  }

  /** Get a sensible default description based on HTTP status code and method. */
  private String getDefaultDescription(String responseCode, String method) {
    try {
      int code = Integer.parseInt(responseCode);
      String methodUpper = method.toUpperCase(Locale.ROOT);

      // Standard HTTP status code descriptions
      switch (code) {
        case 200:
          return "Successful operation";
        case 201:
          return "Resource created successfully";
        case 204:
          return "Operation completed successfully with no content";
        case 400:
          return "Bad request - Invalid input";
        case 401:
          return "Unauthorized - Authentication required";
        case 403:
          return "Forbidden - Insufficient permissions";
        case 404:
          return "Resource not found";
        case 409:
          return "Conflict - Resource already exists";
        case 422:
          return "Unprocessable entity - Validation failed";
        case 500:
          return "Internal server error";
        case 503:
          return "Service unavailable";
        default:
          // Fallback based on code range
          if (code >= 200 && code < 300) {
            return "Successful operation";
          } else if (code >= 400 && code < 500) {
            return "Client error";
          } else if (code >= 500) {
            return "Server error";
          }
          return "Response";
      }
    } catch (NumberFormatException e) {
      return "Response";
    }
  }
}
