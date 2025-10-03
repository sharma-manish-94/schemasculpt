package io.github.sharma_manish_94.schemasculpt_api.controller;

import io.github.sharma_manish_94.schemasculpt_api.dto.ExplanationRequest;
import io.github.sharma_manish_94.schemasculpt_api.dto.ExplanationResponse;
import io.github.sharma_manish_94.schemasculpt_api.service.ai.AIService;
import io.github.sharma_manish_94.schemasculpt_api.service.SessionService;
import io.swagger.v3.oas.models.OpenAPI;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/explanations")
@CrossOrigin(origins = "*")
@Slf4j
public class ExplanationController {

    private final AIService aiService;
    private final SessionService sessionService;
    private final ObjectMapper objectMapper;

    public ExplanationController(AIService aiService, SessionService sessionService, ObjectMapper objectMapper) {
        this.aiService = aiService;
        this.sessionService = sessionService;
        this.objectMapper = objectMapper;
    }

    @PostMapping("/explain")
    public ResponseEntity<ExplanationResponse> explainValidationIssue(
            @RequestBody ExplanationRequest request,
            @RequestParam(required = false) String sessionId) {

        log.info("Generating explanation for rule: {} in category: {}",
                request.ruleId(), request.category());

        try {
            // Get spec from session if available
            String specText = request.specText();
            if (sessionId != null && !sessionId.trim().isEmpty()) {
                try {
                    OpenAPI openAPI = sessionService.getSpecForSession(sessionId);
                    if (openAPI != null) {
                        specText = objectMapper.writeValueAsString(openAPI);
                    }
                } catch (Exception e) {
                    log.warn("Could not retrieve spec from session {}: {}", sessionId, e.getMessage());
                }
            }

            // Prepare request for AI service
            Map<String, Object> aiRequest = new HashMap<>();
            aiRequest.put("rule_id", request.ruleId());
            aiRequest.put("message", request.message());
            aiRequest.put("spec_text", specText);
            aiRequest.put("category", request.category());
            aiRequest.put("context", request.context());

            // Call AI service explanation endpoint
            Map<String, Object> aiResponse = aiService.explainValidationIssue(aiRequest);

            // Convert AI response to our DTO
            ExplanationResponse response = new ExplanationResponse(
                    (String) aiResponse.getOrDefault("explanation", "No explanation available"),
                    (String) aiResponse.getOrDefault("severity", "info"),
                    (String) aiResponse.getOrDefault("category", request.category()),
                    (List<String>) aiResponse.getOrDefault("related_best_practices", List.of()),
                    (List<String>) aiResponse.getOrDefault("example_solutions", List.of()),
                    (List<String>) aiResponse.getOrDefault("additional_resources", List.of()),
                    (Map<String, Object>) aiResponse.getOrDefault("metadata", Map.of())
            );

            log.info("Successfully generated explanation for rule: {}", request.ruleId());
            return ResponseEntity.ok(response);

        } catch (Exception e) {
            log.error("Failed to generate explanation for rule {}: {}", request.ruleId(), e.getMessage(), e);

            // Return a fallback explanation
            ExplanationResponse fallbackResponse = new ExplanationResponse(
                    "An error occurred while generating the explanation. Please try again.",
                    "error",
                    request.category(),
                    List.of(),
                    List.of(),
                    List.of(),
                    Map.of("error", e.getMessage(), "rule_id", request.ruleId())
            );

            return ResponseEntity.status(500).body(fallbackResponse);
        }
    }

    @GetMapping("/health")
    public ResponseEntity<Map<String, Object>> healthCheck() {
        Map<String, Object> health = new HashMap<>();
        health.put("status", "healthy");
        health.put("service", "explanation-controller");
        health.put("timestamp", System.currentTimeMillis());

        return ResponseEntity.ok(health);
    }
}