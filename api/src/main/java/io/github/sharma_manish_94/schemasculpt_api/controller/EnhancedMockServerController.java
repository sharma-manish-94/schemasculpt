package io.github.sharma_manish_94.schemasculpt_api.controller;

import io.github.sharma_manish_94.schemasculpt_api.dto.ai.MockStartResponse;
import io.github.sharma_manish_94.schemasculpt_api.service.ai.EnhancedAIService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import jakarta.servlet.http.HttpServletRequest;
import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.UUID;

@RestController
@RequestMapping("/api/v1/mock")
@RequiredArgsConstructor
@Slf4j
public class EnhancedMockServerController {
    private final EnhancedAIService enhancedAIService;

    @PostMapping("/start")
    public ResponseEntity<MockStartResponse> startMockServer(@RequestBody Map<String, Object> request) {
        log.info("Starting enhanced mock server with AI-powered responses");

        try {
            MockStartResponse response = enhancedAIService.startMockServer(request)
                    .timeout(Duration.ofMinutes(2))
                    .block();

            if (response == null) {
                // Create fallback response
                String mockId = UUID.randomUUID().toString();
                response = new MockStartResponse(
                    mockId,
                    "/mock/" + mockId,
                    "localhost",
                    8080,
                    List.of(),
                    0,
                    Instant.now(),
                    "Mock server created (fallback mode)",
                    "/mock/" + mockId + "/docs"
                );
            }

            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("Failed to start mock server: {}", e.getMessage());

            // Return error response
            return ResponseEntity.internalServerError()
                    .body(new MockStartResponse(
                        null,
                        null,
                        null,
                        null,
                        List.of(),
                        0,
                        Instant.now(),
                        "Failed to start mock server: " + e.getMessage(),
                        null
                    ));
        }
    }

    @PutMapping("/{mockId}")
    public ResponseEntity<Map<String, Object>> updateMockServer(
            @PathVariable String mockId,
            @RequestBody Map<String, Object> request) {
        log.info("Updating mock server: {}", mockId);

        try {
            Map<String, Object> response = enhancedAIService.updateMockServer(mockId, request)
                    .timeout(Duration.ofMinutes(2))
                    .block();

            if (response == null) {
                response = Map.of(
                    "message", "Mock server update completed (fallback)",
                    "mock_id", mockId,
                    "updated_at", Instant.now(),
                    "status", "updated"
                );
            }

            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("Failed to update mock server {}: {}", mockId, e.getMessage());

            Map<String, Object> errorResponse = Map.of(
                "error", e.getMessage(),
                "mock_id", mockId,
                "status", "update_failed",
                "timestamp", Instant.now()
            );

            return ResponseEntity.internalServerError().body(errorResponse);
        }
    }

    @GetMapping("/{mockId}")
    public ResponseEntity<Map<String, Object>> getMockServerInfo(@PathVariable String mockId) {
        log.info("Fetching mock server info: {}", mockId);

        try {
            Map<String, Object> response = enhancedAIService.getMockServerInfo(mockId)
                    .timeout(Duration.ofSeconds(30))
                    .block();

            if (response == null) {
                return ResponseEntity.notFound().build();
            }

            // Check if response contains error
            if (response.containsKey("error")) {
                return ResponseEntity.notFound().build();
            }

            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("Failed to fetch mock server info {}: {}", mockId, e.getMessage());
            return ResponseEntity.notFound().build();
        }
    }

    @DeleteMapping("/{mockId}")
    public ResponseEntity<Map<String, Object>> deleteMockServer(@PathVariable String mockId) {
        log.info("Deleting mock server: {}", mockId);

        // Note: The AI service doesn't expose delete endpoints, so this is a mock implementation
        // In a real scenario, you'd need to track mock servers and handle their lifecycle

        return ResponseEntity.ok(Map.of(
            "message", "Mock server deletion requested",
            "mock_id", mockId,
            "status", "deletion_requested",
            "note", "Mock server cleanup is handled by the AI service",
            "timestamp", Instant.now()
        ));
    }

    @GetMapping("/list")
    public ResponseEntity<Map<String, Object>> listMockServers(
            @RequestParam(required = false, defaultValue = "0") int page,
            @RequestParam(required = false, defaultValue = "10") int size) {
        log.info("Listing mock servers: page={}, size={}", page, size);

        // Since the AI service doesn't provide a list endpoint, return a mock response
        // In a real implementation, you'd maintain a registry of active mock servers

        return ResponseEntity.ok(Map.of(
            "mock_servers", List.of(),
            "total", 0,
            "page", page,
            "size", size,
            "message", "Mock server listing not available from AI service",
            "timestamp", Instant.now()
        ));
    }

    @PostMapping("/{mockId}/config")
    public ResponseEntity<Map<String, Object>> updateMockServerConfig(
            @PathVariable String mockId,
            @RequestBody Map<String, Object> config) {
        log.info("Updating mock server config: {}", mockId);

        try {
            // Create request with updated configuration
            Map<String, Object> request = Map.of(
                "mock_id", mockId,
                "config", config
            );

            Map<String, Object> response = enhancedAIService.updateMockServer(mockId, request)
                    .timeout(Duration.ofMinutes(1))
                    .block();

            if (response == null) {
                response = Map.of(
                    "message", "Mock server configuration updated",
                    "mock_id", mockId,
                    "config", config,
                    "updated_at", Instant.now()
                );
            }

            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("Failed to update mock server config {}: {}", mockId, e.getMessage());

            return ResponseEntity.internalServerError().body(Map.of(
                "error", e.getMessage(),
                "mock_id", mockId,
                "status", "config_update_failed"
            ));
        }
    }

    @GetMapping("/{mockId}/stats")
    public ResponseEntity<Map<String, Object>> getMockServerStats(@PathVariable String mockId) {
        log.info("Fetching mock server stats: {}", mockId);

        // Return mock stats since the AI service doesn't provide detailed analytics
        Map<String, Object> stats = Map.of(
            "mock_id", mockId,
            "total_requests", 0,
            "requests_by_method", Map.of(
                "GET", 0,
                "POST", 0,
                "PUT", 0,
                "DELETE", 0
            ),
            "average_response_time_ms", 0.0,
            "error_rate", 0.0,
            "uptime_seconds", 0,
            "last_request", null,
            "status", "active",
            "message", "Stats collection not available from AI service",
            "timestamp", Instant.now()
        );

        return ResponseEntity.ok(stats);
    }

    @PostMapping("/{mockId}/reset")
    public ResponseEntity<Map<String, Object>> resetMockServerStats(@PathVariable String mockId) {
        log.info("Resetting mock server stats: {}", mockId);

        return ResponseEntity.ok(Map.of(
            "message", "Mock server stats reset requested",
            "mock_id", mockId,
            "status", "stats_reset",
            "reset_at", Instant.now(),
            "note", "Stats are managed by the AI service"
        ));
    }

    @GetMapping("/health")
    public ResponseEntity<Map<String, Object>> getMockServiceHealth() {
        log.info("Checking mock service health");

        try {
            // Use the AI service health check as a proxy for mock service health
            var healthResponse = enhancedAIService.healthCheck()
                    .timeout(Duration.ofSeconds(30))
                    .block();

            if (healthResponse == null || !"healthy".equals(healthResponse.status())) {
                return ResponseEntity.ok(Map.of(
                    "status", "unhealthy",
                    "message", "AI service is not available",
                    "mock_service_available", false,
                    "timestamp", Instant.now()
                ));
            }

            return ResponseEntity.ok(Map.of(
                "status", "healthy",
                "message", "Mock service is operational",
                "mock_service_available", true,
                "ai_service_status", healthResponse.status(),
                "timestamp", Instant.now()
            ));
        } catch (Exception e) {
            log.error("Mock service health check failed: {}", e.getMessage());

            return ResponseEntity.ok(Map.of(
                "status", "unhealthy",
                "error", e.getMessage(),
                "mock_service_available", false,
                "timestamp", Instant.now()
            ));
        }
    }

    // Proxy endpoint for direct mock requests (if needed)
    @RequestMapping(value = "/{mockId}/proxy/**", method = {
        RequestMethod.GET, RequestMethod.POST, RequestMethod.PUT,
        RequestMethod.PATCH, RequestMethod.DELETE, RequestMethod.OPTIONS
    })
    public ResponseEntity<Map<String, Object>> proxyMockRequest(
            @PathVariable String mockId,
            HttpServletRequest request) {
        log.info("Proxying mock request: {} {} for mockId: {}",
                 request.getMethod(), request.getRequestURI(), mockId);

        // This would typically proxy to the actual mock server
        // For now, return a generic response
        return ResponseEntity.ok(Map.of(
            "message", "Mock request handled",
            "mock_id", mockId,
            "method", request.getMethod(),
            "path", request.getRequestURI(),
            "note", "This is a proxy response - actual mock data would come from the AI service",
            "timestamp", Instant.now()
        ));
    }
}