package io.github.sharma_manish_94.schemasculpt_api.service;

import io.github.sharma_manish_94.schemasculpt_api.dto.HardeningResponse;
import io.github.sharma_manish_94.schemasculpt_api.dto.request.HardenOperationRequest;
import io.swagger.v3.oas.models.Components;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.Operation;
import io.swagger.v3.oas.models.PathItem;
import io.swagger.v3.oas.models.headers.Header;
import io.swagger.v3.oas.models.media.Content;
import io.swagger.v3.oas.models.media.MediaType;
import io.swagger.v3.oas.models.media.Schema;
import io.swagger.v3.oas.models.parameters.HeaderParameter;
import io.swagger.v3.oas.models.parameters.Parameter;
import io.swagger.v3.oas.models.responses.ApiResponse;
import io.swagger.v3.oas.models.responses.ApiResponses;
import io.swagger.v3.oas.models.security.SecurityRequirement;
import io.swagger.v3.oas.models.security.SecurityScheme;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

@Service
@Slf4j
public class HardeningService {

  private final SessionService sessionService;

  public HardeningService(SessionService sessionService) {
    this.sessionService = sessionService;
  }

  public HardeningResponse hardenOperation(String sessionId, HardenOperationRequest request) {
    log.info(
        "Hardening operation {} {} with patterns: {}",
        request.method(),
        request.path(),
        request.patterns());

    OpenAPI openAPI = sessionService.getSpecForSession(sessionId);
    if (openAPI == null) {
      throw new IllegalArgumentException("Invalid session ID: " + sessionId);
    }

    PathItem pathItem = openAPI.getPaths().get(request.path());
    if (pathItem == null) {
      throw new IllegalArgumentException("Path not found: " + request.path());
    }

    Operation operation = getOperationByMethod(pathItem, request.method());
    if (operation == null) {
      throw new IllegalArgumentException(
          "Operation not found: " + request.method() + " " + request.path());
    }

    List<String> appliedPatterns = new ArrayList<>();
    Map<String, Object> changes = new HashMap<>();
    List<String> warnings = new ArrayList<>();

    // Apply security patterns
    if (request.options().addOAuth2()) {
      applyOAuth2Security(openAPI, operation, changes, warnings);
      appliedPatterns.add("OAuth2");
    }

    // Apply rate limiting
    if (request.options().addRateLimiting()) {
      applyRateLimiting(operation, request.options().rateLimitPolicy(), changes);
      appliedPatterns.add("Rate Limiting");
    }

    // Apply caching
    if (request.options().addCaching()) {
      applyCaching(operation, request.options().cacheTTL(), changes);
      appliedPatterns.add("Caching");
    }

    // Apply idempotency
    if (request.options().addIdempotency()) {
      applyIdempotency(operation, changes);
      appliedPatterns.add("Idempotency");
    }

    // Apply validation
    if (request.options().addValidation()) {
      applyValidation(operation, changes);
      appliedPatterns.add("Validation");
    }

    // Apply error handling
    if (request.options().addErrorHandling()) {
      applyErrorHandling(operation, changes);
      appliedPatterns.add("Error Handling");
    }

    // Update the session with modified spec
    sessionService.updateSessionSpec(sessionId, openAPI);

    log.info(
        "Successfully applied {} patterns to {} {}",
        appliedPatterns.size(),
        request.method(),
        request.path());

    return new HardeningResponse(
        request.path(), request.method(), appliedPatterns, changes, warnings, true);
  }

  private Operation getOperationByMethod(PathItem pathItem, String method) {
    return switch (method.toUpperCase()) {
      case "GET" -> pathItem.getGet();
      case "POST" -> pathItem.getPost();
      case "PUT" -> pathItem.getPut();
      case "PATCH" -> pathItem.getPatch();
      case "DELETE" -> pathItem.getDelete();
      case "OPTIONS" -> pathItem.getOptions();
      case "HEAD" -> pathItem.getHead();
      case "TRACE" -> pathItem.getTrace();
      default -> null;
    };
  }

  private void applyOAuth2Security(
      OpenAPI openAPI, Operation operation, Map<String, Object> changes, List<String> warnings) {
    // Add OAuth2 security scheme to components if not exists
    if (openAPI.getComponents() == null) {
      openAPI.setComponents(new Components());
    }

    if (openAPI.getComponents().getSecuritySchemes() == null) {
      openAPI.getComponents().setSecuritySchemes(new HashMap<>());
    }

    String schemeName = "oauth2";
    if (!openAPI.getComponents().getSecuritySchemes().containsKey(schemeName)) {
      SecurityScheme oauth2Scheme =
          new SecurityScheme()
              .type(SecurityScheme.Type.OAUTH2)
              .description("OAuth2 authentication")
              .flows(
                  new io.swagger.v3.oas.models.security.OAuthFlows()
                      .authorizationCode(
                          new io.swagger.v3.oas.models.security.OAuthFlow()
                              .authorizationUrl("https://auth.example.com/oauth2/authorize")
                              .tokenUrl("https://auth.example.com/oauth2/token")
                              .scopes(
                                  new io.swagger.v3.oas.models.security.Scopes()
                                      .addString("read", "Read access")
                                      .addString("write", "Write access"))));

      openAPI.getComponents().getSecuritySchemes().put(schemeName, oauth2Scheme);
      changes.put("oauth2_scheme_added", true);
    } else {
      warnings.add("OAuth2 security scheme already exists");
    }

    // Add security requirement to operation
    if (operation.getSecurity() == null) {
      operation.setSecurity(new ArrayList<>());
    }

    SecurityRequirement securityRequirement = new SecurityRequirement();
    securityRequirement.addList(schemeName, List.of("read", "write"));

    if (!operation.getSecurity().contains(securityRequirement)) {
      operation.getSecurity().add(securityRequirement);
      changes.put("oauth2_requirement_added", true);
    } else {
      warnings.add("OAuth2 security requirement already exists");
    }
  }

  private void applyRateLimiting(
      Operation operation, String rateLimitPolicy, Map<String, Object> changes) {
    // Add rate limiting headers to responses
    if (operation.getResponses() == null) {
      operation.setResponses(new ApiResponses());
    }

    String rateLimit = rateLimitPolicy != null ? rateLimitPolicy : "100/hour";

    for (ApiResponse response : operation.getResponses().values()) {
      if (response.getHeaders() == null) {
        response.setHeaders(new HashMap<>());
      }

      // Add rate limiting headers
      response
          .getHeaders()
          .put(
              "X-RateLimit-Limit",
              new Header()
                  .description("Request limit per hour")
                  .schema(new Schema<>().type("integer")));
      response
          .getHeaders()
          .put(
              "X-RateLimit-Remaining",
              new Header()
                  .description("Remaining requests")
                  .schema(new Schema<>().type("integer")));
      response
          .getHeaders()
          .put(
              "X-RateLimit-Reset",
              new Header().description("Reset time").schema(new Schema<>().type("integer")));
    }

    // Add 429 response for rate limit exceeded
    if (!operation.getResponses().containsKey("429")) {
      ApiResponse rateLimitResponse =
          new ApiResponse()
              .description("Too Many Requests - Rate limit exceeded")
              .content(
                  new Content()
                      .addMediaType(
                          "application/json",
                          new MediaType()
                              .schema(
                                  new Schema<>()
                                      .type("object")
                                      .addProperty(
                                          "error",
                                          new Schema<>()
                                              .type("string")
                                              .example("Rate limit exceeded"))
                                      .addProperty(
                                          "retry_after",
                                          new Schema<>().type("integer").example(3600)))));

      operation.getResponses().put("429", rateLimitResponse);
    }

    changes.put("rate_limiting_added", true);
    changes.put("rate_limit_policy", rateLimit);
  }

  private void applyCaching(Operation operation, String cacheTTL, Map<String, Object> changes) {
    if (!"GET"
        .equalsIgnoreCase(
            operation.getTags() != null && !operation.getTags().isEmpty()
                ? operation.getTags().get(0)
                : "GET")) {
      // Only apply caching to GET operations primarily
      return;
    }

    String ttl = cacheTTL != null ? cacheTTL : "300"; // 5 minutes default

    // Add cache control headers to 200 response
    ApiResponse successResponse = operation.getResponses().get("200");
    if (successResponse != null) {
      if (successResponse.getHeaders() == null) {
        successResponse.setHeaders(new HashMap<>());
      }

      successResponse
          .getHeaders()
          .put(
              "Cache-Control",
              new Header()
                  .description("Cache control directives")
                  .schema(new Schema<>().type("string").example("max-age=" + ttl)));
      successResponse
          .getHeaders()
          .put(
              "ETag",
              new Header()
                  .description("Entity tag for cache validation")
                  .schema(new Schema<>().type("string")));
    }

    // Add conditional headers as parameters
    if (operation.getParameters() == null) {
      operation.setParameters(new ArrayList<>());
    }

    Parameter ifNoneMatch =
        new HeaderParameter()
            .name("If-None-Match")
            .description("Conditional request header for cache validation")
            .required(false)
            .schema(new Schema<>().type("string"));

    if (operation.getParameters().stream().noneMatch(p -> "If-None-Match".equals(p.getName()))) {
      operation.getParameters().add(ifNoneMatch);
    }

    // Add 304 Not Modified response
    if (!operation.getResponses().containsKey("304")) {
      operation
          .getResponses()
          .put(
              "304",
              new ApiResponse().description("Not Modified - Resource has not been modified"));
    }

    changes.put("caching_added", true);
    changes.put("cache_ttl", ttl);
  }

  private void applyIdempotency(Operation operation, Map<String, Object> changes) {
    // Add idempotency key for POST/PUT/PATCH operations
    String method =
        operation.getTags() != null && !operation.getTags().isEmpty()
            ? operation.getTags().get(0)
            : "";

    if (List.of("POST", "PUT", "PATCH").contains(method.toUpperCase())) {
      if (operation.getParameters() == null) {
        operation.setParameters(new ArrayList<>());
      }

      Parameter idempotencyKey =
          new HeaderParameter()
              .name("Idempotency-Key")
              .description("Unique key to ensure request idempotency")
              .required(true)
              .schema(new Schema<>().type("string").format("uuid"));

      if (operation.getParameters().stream()
          .noneMatch(p -> "Idempotency-Key".equals(p.getName()))) {
        operation.getParameters().add(idempotencyKey);
      }

      changes.put("idempotency_added", true);
    }
  }

  private void applyValidation(Operation operation, Map<String, Object> changes) {
    // Add 400 Bad Request response for validation errors
    if (!operation.getResponses().containsKey("400")) {
      ApiResponse validationErrorResponse =
          new ApiResponse()
              .description("Bad Request - Validation failed")
              .content(
                  new Content()
                      .addMediaType(
                          "application/json",
                          new MediaType()
                              .schema(
                                  new Schema<>()
                                      .type("object")
                                      .addProperty(
                                          "error",
                                          new Schema<>()
                                              .type("string")
                                              .example("Validation failed"))
                                      .addProperty(
                                          "details",
                                          new Schema<>()
                                              .type("array")
                                              .items(
                                                  new Schema<>()
                                                      .type("object")
                                                      .addProperty(
                                                          "field", new Schema<>().type("string"))
                                                      .addProperty(
                                                          "message",
                                                          new Schema<>().type("string")))))));

      operation.getResponses().put("400", validationErrorResponse);
      changes.put("validation_error_response_added", true);
    }
  }

  private void applyErrorHandling(Operation operation, Map<String, Object> changes) {
    // Add standard error responses
    if (!operation.getResponses().containsKey("401")) {
      operation
          .getResponses()
          .put("401", new ApiResponse().description("Unauthorized - Authentication required"));
    }

    if (!operation.getResponses().containsKey("403")) {
      operation
          .getResponses()
          .put("403", new ApiResponse().description("Forbidden - Access denied"));
    }

    if (!operation.getResponses().containsKey("500")) {
      ApiResponse serverErrorResponse =
          new ApiResponse()
              .description("Internal Server Error")
              .content(
                  new Content()
                      .addMediaType(
                          "application/json",
                          new MediaType()
                              .schema(
                                  new Schema<>()
                                      .type("object")
                                      .addProperty(
                                          "error",
                                          new Schema<>()
                                              .type("string")
                                              .example("Internal server error"))
                                      .addProperty(
                                          "timestamp",
                                          new Schema<>().type("string").format("date-time"))
                                      .addProperty(
                                          "request_id",
                                          new Schema<>().type("string").format("uuid")))));

      operation.getResponses().put("500", serverErrorResponse);
    }

    changes.put("standard_error_responses_added", true);
  }
}
