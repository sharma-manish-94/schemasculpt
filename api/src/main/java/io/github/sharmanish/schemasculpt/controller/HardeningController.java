package io.github.sharmanish.schemasculpt.controller;

import io.github.sharmanish.schemasculpt.dto.HardeningResponse;
import io.github.sharmanish.schemasculpt.dto.request.HardenOperationRequest;
import io.github.sharmanish.schemasculpt.service.HardeningService;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/sessions/{sessionId}/hardening")
@CrossOrigin(origins = "*")
@Slf4j
public class HardeningController {

  private final HardeningService hardeningService;

  public HardeningController(HardeningService hardeningService) {
    this.hardeningService = hardeningService;
  }

  @PostMapping("/operations/oauth2")
  public ResponseEntity<HardeningResponse> addOAuth2Security(
      @PathVariable String sessionId, @RequestBody Map<String, String> request) {

    String path = request.get("path");
    String method = request.get("method");

    HardenOperationRequest hardenRequest =
        new HardenOperationRequest(
            path,
            method,
            List.of("oauth2"),
            new HardenOperationRequest.HardeningOptions(
                true, false, false, false, false, false, null, null, "oauth2"));

    return hardenOperation(sessionId, hardenRequest);
  }

  @PostMapping("/operations")
  public ResponseEntity<HardeningResponse> hardenOperation(
      @PathVariable String sessionId, @RequestBody HardenOperationRequest request) {

    log.info(
        "Hardening operation {} {} for session {}", request.method(), request.path(), sessionId);

    try {
      HardeningResponse response = hardeningService.hardenOperation(sessionId, request);
      return ResponseEntity.ok(response);
    } catch (IllegalArgumentException e) {
      log.error("Invalid request for hardening: {}", e.getMessage());
      return ResponseEntity.badRequest()
          .body(
              new HardeningResponse(
                  request.path(),
                  request.method(),
                  List.of(),
                  Map.of(),
                  List.of(e.getMessage()),
                  false));
    } catch (Exception e) {
      log.error("Failed to harden operation {}: {}", request.path(), e.getMessage(), e);
      return ResponseEntity.status(500)
          .body(
              new HardeningResponse(
                  request.path(),
                  request.method(),
                  List.of(),
                  Map.of("error", e.getMessage()),
                  List.of("Internal server error"),
                  false));
    }
  }

  @PostMapping("/operations/rate-limiting")
  public ResponseEntity<HardeningResponse> addRateLimiting(
      @PathVariable String sessionId, @RequestBody Map<String, String> request) {

    String path = request.get("path");
    String method = request.get("method");
    String policy = request.getOrDefault("policy", "100/hour");

    HardenOperationRequest hardenRequest =
        new HardenOperationRequest(
            path,
            method,
            List.of("rate-limiting"),
            new HardenOperationRequest.HardeningOptions(
                false, true, false, false, false, false, policy, null, null));

    return hardenOperation(sessionId, hardenRequest);
  }

  @PostMapping("/operations/caching")
  public ResponseEntity<HardeningResponse> addCaching(
      @PathVariable String sessionId, @RequestBody Map<String, String> request) {

    String path = request.get("path");
    String method = request.get("method");
    String ttl = request.getOrDefault("ttl", "300");

    HardenOperationRequest hardenRequest =
        new HardenOperationRequest(
            path,
            method,
            List.of("caching"),
            new HardenOperationRequest.HardeningOptions(
                false, false, true, false, false, false, null, ttl, null));

    return hardenOperation(sessionId, hardenRequest);
  }

  @PostMapping("/operations/complete")
  public ResponseEntity<HardeningResponse> hardenOperationComplete(
      @PathVariable String sessionId, @RequestBody Map<String, String> request) {

    String path = request.get("path");
    String method = request.get("method");

    HardenOperationRequest hardenRequest =
        new HardenOperationRequest(
            path,
            method,
            List.of(
                "oauth2",
                "rate-limiting",
                "caching",
                "idempotency",
                "validation",
                "error-handling"),
            new HardenOperationRequest.HardeningOptions(
                true, true, true, true, true, true, "100/hour", "300", "oauth2"));

    return hardenOperation(sessionId, hardenRequest);
  }

  @GetMapping("/patterns")
  public ResponseEntity<Map<String, Object>> getAvailablePatterns() {
    Map<String, Object> patterns = new HashMap<>();

    patterns.put(
        "oauth2",
        Map.of(
            "name", "OAuth2 Security",
            "description", "Add OAuth2 authentication and authorization",
            "applicable_methods", List.of("GET", "POST", "PUT", "PATCH", "DELETE")));

    patterns.put(
        "rate-limiting",
        Map.of(
            "name", "Rate Limiting",
            "description", "Add rate limiting headers and 429 response",
            "applicable_methods", List.of("GET", "POST", "PUT", "PATCH", "DELETE")));

    patterns.put(
        "caching",
        Map.of(
            "name", "HTTP Caching",
            "description", "Add cache control headers and 304 response",
            "applicable_methods", List.of("GET")));

    patterns.put(
        "idempotency",
        Map.of(
            "name", "Idempotency",
            "description", "Add idempotency key for safe retries",
            "applicable_methods", List.of("POST", "PUT", "PATCH")));

    patterns.put(
        "validation",
        Map.of(
            "name", "Input Validation",
            "description", "Add validation error responses",
            "applicable_methods", List.of("POST", "PUT", "PATCH")));

    patterns.put(
        "error-handling",
        Map.of(
            "name", "Standard Error Handling",
            "description", "Add standard HTTP error responses",
            "applicable_methods", List.of("GET", "POST", "PUT", "PATCH", "DELETE")));

    return ResponseEntity.ok(
        Map.of(
            "patterns",
            patterns,
            "recommendations",
            Map.of(
                "GET", List.of("oauth2", "rate-limiting", "caching", "error-handling"),
                "POST",
                List.of(
                    "oauth2", "rate-limiting", "idempotency", "validation", "error-handling"),
                "PUT",
                List.of(
                    "oauth2", "rate-limiting", "idempotency", "validation", "error-handling"),
                "PATCH",
                List.of(
                    "oauth2", "rate-limiting", "idempotency", "validation", "error-handling"),
                "DELETE", List.of("oauth2", "rate-limiting", "error-handling"))));
  }

  @GetMapping("/health")
  public ResponseEntity<Map<String, Object>> healthCheck() {
    Map<String, Object> health = new HashMap<>();
    health.put("status", "healthy");
    health.put("service", "hardening-controller");
    health.put("timestamp", System.currentTimeMillis());

    return ResponseEntity.ok(health);
  }
}
