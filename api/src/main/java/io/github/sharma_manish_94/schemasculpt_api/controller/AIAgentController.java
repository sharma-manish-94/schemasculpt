package io.github.sharma_manish_94.schemasculpt_api.controller;

import io.github.sharma_manish_94.schemasculpt_api.service.ai.EnhancedAIService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/ai/agents")
@RequiredArgsConstructor
@Slf4j
public class AIAgentController {
    private final EnhancedAIService enhancedAIService;

    @GetMapping("/status")
    public ResponseEntity<Map<String, Object>> getAgentsStatus() {
        log.info("Fetching AI agents status");

        try {
            Map<String, Object> agentStatus = enhancedAIService.getAgentsStatus()
                    .timeout(Duration.ofSeconds(30))
                    .block();

            if (agentStatus == null) {
                agentStatus = createFallbackStatus();
            }

            // Enhance the response with additional metadata
            agentStatus = enhanceStatusResponse(agentStatus);

            return ResponseEntity.ok(agentStatus);
        } catch (Exception e) {
            log.error("Failed to fetch agents status: {}", e.getMessage());

            Map<String, Object> errorResponse = createErrorStatus(e.getMessage());
            return ResponseEntity.ok(errorResponse);
        }
    }

    @GetMapping("/{agentName}/status")
    public ResponseEntity<Map<String, Object>> getSpecificAgentStatus(@PathVariable String agentName) {
        log.info("Fetching status for specific agent: {}", agentName);

        try {
            Map<String, Object> allAgentsStatus = enhancedAIService.getAgentsStatus()
                    .timeout(Duration.ofSeconds(30))
                    .block();

            if (allAgentsStatus == null) {
                return ResponseEntity.ok(createAgentNotFoundResponse(agentName));
            }

            // Extract specific agent status
            Map<String, Object> agents = (Map<String, Object>) allAgentsStatus.get("agents");
            if (agents != null && agents.containsKey(agentName)) {
                Map<String, Object> agentInfo = (Map<String, Object>) agents.get(agentName);
                return ResponseEntity.ok(Map.of(
                    "agent_name", agentName,
                    "status", agentInfo.getOrDefault("status", "unknown"),
                    "details", agentInfo,
                    "last_updated", Instant.now()
                ));
            } else {
                return ResponseEntity.ok(createAgentNotFoundResponse(agentName));
            }
        } catch (Exception e) {
            log.error("Failed to fetch status for agent {}: {}", agentName, e.getMessage());

            return ResponseEntity.ok(Map.of(
                "agent_name", agentName,
                "status", "error",
                "error_message", e.getMessage(),
                "last_updated", Instant.now()
            ));
        }
    }

    @PostMapping("/{agentName}/restart")
    public ResponseEntity<Map<String, Object>> restartAgent(@PathVariable String agentName) {
        log.info("Attempting to restart agent: {}", agentName);

        // Note: The AI service doesn't expose restart endpoints, so this is a mock response
        // In a real implementation, you would need actual agent management capabilities

        return ResponseEntity.ok(Map.of(
            "message", "Agent restart requested",
            "agent_name", agentName,
            "status", "restart_requested",
            "note", "Agent restart is handled by the AI service internally",
            "timestamp", Instant.now()
        ));
    }

    @GetMapping("/performance")
    public ResponseEntity<Map<String, Object>> getAgentsPerformance() {
        log.info("Fetching AI agents performance metrics");

        try {
            Map<String, Object> agentStatus = enhancedAIService.getAgentsStatus()
                    .timeout(Duration.ofSeconds(30))
                    .block();

            if (agentStatus == null) {
                return ResponseEntity.ok(createFallbackPerformanceMetrics());
            }

            // Extract and enhance performance data
            Map<String, Object> performanceMetrics = extractPerformanceMetrics(agentStatus);

            return ResponseEntity.ok(performanceMetrics);
        } catch (Exception e) {
            log.error("Failed to fetch agents performance: {}", e.getMessage());

            return ResponseEntity.ok(Map.of(
                "error", e.getMessage(),
                "performance_data", "unavailable",
                "timestamp", Instant.now()
            ));
        }
    }

    @GetMapping("/capabilities")
    public ResponseEntity<Map<String, Object>> getAgentsCapabilities() {
        log.info("Fetching AI agents capabilities");

        // Return predefined capabilities since they're relatively static
        Map<String, Object> capabilities = Map.of(
            "agents", Map.of(
                "specification_agent", Map.of(
                    "name", "Specification Agent",
                    "description", "Handles OpenAPI specification modifications and enhancements",
                    "capabilities", List.of(
                        "spec_modification", "validation", "optimization", "documentation_generation"
                    )
                ),
                "generation_agent", Map.of(
                    "name", "Generation Agent",
                    "description", "Generates complete OpenAPI specifications from descriptions",
                    "capabilities", List.of(
                        "spec_generation", "schema_creation", "endpoint_design", "example_generation"
                    )
                ),
                "validation_agent", Map.of(
                    "name", "Validation Agent",
                    "description", "Validates and analyzes OpenAPI specifications",
                    "capabilities", List.of(
                        "spec_validation", "error_detection", "compliance_checking", "best_practices"
                    )
                ),
                "mock_agent", Map.of(
                    "name", "Mock Agent",
                    "description", "Generates realistic mock data and responses",
                    "capabilities", List.of(
                        "mock_data_generation", "response_simulation", "realistic_examples", "data_variety"
                    )
                )
            ),
            "total_agents", 4,
            "framework_version", "1.0.0",
            "last_updated", Instant.now()
        );

        return ResponseEntity.ok(capabilities);
    }

    // Helper methods

    private Map<String, Object> createFallbackStatus() {
        return Map.of(
            "status", "unavailable",
            "message", "Agent status unavailable - AI service may be offline",
            "agents", Map.of(),
            "total_agents", 0,
            "active_agents", 0,
            "timestamp", Instant.now()
        );
    }

    private Map<String, Object> enhanceStatusResponse(Map<String, Object> originalStatus) {
        return Map.of(
            "overall_status", originalStatus.getOrDefault("overall_status", "unknown"),
            "agents", originalStatus.getOrDefault("agents", Map.of()),
            "total_agents", calculateTotalAgents(originalStatus),
            "active_agents", calculateActiveAgents(originalStatus),
            "last_health_check", Instant.now(),
            "service_availability", originalStatus.containsKey("error") ? "degraded" : "available"
        );
    }

    private Map<String, Object> createErrorStatus(String errorMessage) {
        return Map.of(
            "status", "error",
            "error_message", errorMessage,
            "agents", Map.of(),
            "total_agents", 0,
            "active_agents", 0,
            "service_availability", "unavailable",
            "timestamp", Instant.now()
        );
    }

    private Map<String, Object> createAgentNotFoundResponse(String agentName) {
        return Map.of(
            "agent_name", agentName,
            "status", "not_found",
            "message", "Agent not found or not available",
            "available_agents", List.of("specification_agent", "generation_agent", "validation_agent", "mock_agent"),
            "timestamp", Instant.now()
        );
    }

    private Map<String, Object> createFallbackPerformanceMetrics() {
        return Map.of(
            "overall_performance", "unavailable",
            "agent_metrics", Map.of(),
            "average_response_time", 0,
            "success_rate", 0.0,
            "total_requests", 0,
            "timestamp", Instant.now()
        );
    }

    private Map<String, Object> extractPerformanceMetrics(Map<String, Object> agentStatus) {
        // Extract performance data from agent status
        Map<String, Object> agents = (Map<String, Object>) agentStatus.get("agents");

        if (agents == null) {
            return createFallbackPerformanceMetrics();
        }

        return Map.of(
            "overall_performance", agentStatus.getOrDefault("overall_status", "unknown"),
            "agent_metrics", agents,
            "total_agents_monitored", agents.size(),
            "performance_score", calculateOverallPerformanceScore(agents),
            "last_measurement", Instant.now()
        );
    }

    private int calculateTotalAgents(Map<String, Object> status) {
        Map<String, Object> agents = (Map<String, Object>) status.get("agents");
        return agents != null ? agents.size() : 0;
    }

    private int calculateActiveAgents(Map<String, Object> status) {
        Map<String, Object> agents = (Map<String, Object>) status.get("agents");
        if (agents == null) return 0;

        return (int) agents.values().stream()
                .filter(agent -> {
                    if (agent instanceof Map) {
                        Map<String, Object> agentMap = (Map<String, Object>) agent;
                        return "active".equals(agentMap.get("status")) || "healthy".equals(agentMap.get("status"));
                    }
                    return false;
                })
                .count();
    }

    private double calculateOverallPerformanceScore(Map<String, Object> agents) {
        if (agents.isEmpty()) {
            return 0.0;
        }

        // Simple scoring based on agent availability
        double totalScore = agents.values().stream()
                .mapToDouble(agent -> {
                    if (agent instanceof Map) {
                        Map<String, Object> agentMap = (Map<String, Object>) agent;
                        String status = (String) agentMap.get("status");
                        return "active".equals(status) || "healthy".equals(status) ? 100.0 : 0.0;
                    }
                    return 0.0;
                })
                .average()
                .orElse(0.0);

        return Math.round(totalScore * 100.0) / 100.0;
    }
}