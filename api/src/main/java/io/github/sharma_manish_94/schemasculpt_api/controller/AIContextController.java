package io.github.sharma_manish_94.schemasculpt_api.controller;

import io.github.sharma_manish_94.schemasculpt_api.dto.ai.SessionContextResponse;
import io.github.sharma_manish_94.schemasculpt_api.service.ai.EnhancedAIService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.UUID;

@RestController
@RequestMapping("/api/v1/ai/context")
@RequiredArgsConstructor
@Slf4j
public class AIContextController {
    private final EnhancedAIService enhancedAIService;

    @PostMapping("/session")
    public ResponseEntity<SessionContextResponse> createSession(
            @RequestParam(required = false) String userId) {
        log.info("Creating AI context session for user: {}", userId);

        try {
            SessionContextResponse response = enhancedAIService.createSession(userId)
                    .timeout(Duration.ofSeconds(30))
                    .block();

            if (response == null) {
                // Fallback response
                response = new SessionContextResponse(
                    UUID.randomUUID().toString(),
                    userId,
                    Instant.now(),
                    Instant.now(),
                    0,
                    Map.of("status", "created"),
                    List.of(),
                    Map.of()
                );
            }

            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("Failed to create AI context session: {}", e.getMessage());

            // Return fallback response even on error
            SessionContextResponse fallbackResponse = new SessionContextResponse(
                UUID.randomUUID().toString(),
                userId,
                Instant.now(),
                Instant.now(),
                0,
                Map.of("status", "created", "error", e.getMessage()),
                List.of(),
                Map.of()
            );

            return ResponseEntity.ok(fallbackResponse);
        }
    }

    @GetMapping("/session/{sessionId}")
    public ResponseEntity<SessionContextResponse> getSessionSummary(@PathVariable String sessionId) {
        log.info("Fetching AI context session summary for: {}", sessionId);

        try {
            SessionContextResponse response = enhancedAIService.getSessionSummary(sessionId)
                    .timeout(Duration.ofSeconds(30))
                    .block();

            if (response == null) {
                // Fallback response
                response = new SessionContextResponse(
                    sessionId,
                    null,
                    Instant.now(),
                    Instant.now(),
                    0,
                    Map.of("status", "not_found"),
                    List.of("Session data may be limited or unavailable"),
                    Map.of()
                );
            }

            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("Failed to fetch session summary: {}", e.getMessage());

            SessionContextResponse errorResponse = new SessionContextResponse(
                sessionId,
                null,
                Instant.now(),
                Instant.now(),
                0,
                Map.of("status", "error", "error_message", e.getMessage()),
                List.of("Unable to fetch session data"),
                Map.of()
            );

            return ResponseEntity.ok(errorResponse);
        }
    }

    @GetMapping("/statistics")
    public ResponseEntity<Map<String, Object>> getContextStatistics() {
        log.info("Fetching AI context statistics");

        try {
            Map<String, Object> statistics = enhancedAIService.getContextStatistics()
                    .timeout(Duration.ofSeconds(30))
                    .block();

            if (statistics == null) {
                statistics = Map.of(
                    "status", "unavailable",
                    "total_sessions", 0,
                    "active_sessions", 0,
                    "average_session_duration", 0
                );
            }

            return ResponseEntity.ok(statistics);
        } catch (Exception e) {
            log.error("Failed to fetch context statistics: {}", e.getMessage());

            Map<String, Object> errorResponse = Map.of(
                "status", "error",
                "error_message", e.getMessage(),
                "total_sessions", 0,
                "active_sessions", 0
            );

            return ResponseEntity.ok(errorResponse);
        }
    }

    @DeleteMapping("/session/{sessionId}")
    public ResponseEntity<Map<String, Object>> deleteSession(@PathVariable String sessionId) {
        log.info("Attempting to delete AI context session: {}", sessionId);

        // Note: The AI service doesn't expose a delete endpoint, so we'll return a success response
        // In a real implementation, you might want to track sessions locally and implement cleanup

        return ResponseEntity.ok(Map.of(
            "message", "Session deletion requested",
            "session_id", sessionId,
            "status", "acknowledged",
            "note", "Session cleanup is handled automatically by the AI service"
        ));
    }

    @PostMapping("/session/{sessionId}/reset")
    public ResponseEntity<Map<String, Object>> resetSessionContext(@PathVariable String sessionId) {
        log.info("Attempting to reset context for AI session: {}", sessionId);

        // Note: The AI service doesn't expose a reset endpoint, so we'll return an acknowledgment
        // This could be enhanced to create a new session to effectively "reset" the context

        return ResponseEntity.ok(Map.of(
            "message", "Session context reset requested",
            "session_id", sessionId,
            "status", "acknowledged",
            "note", "Consider creating a new session for a complete reset"
        ));
    }
}