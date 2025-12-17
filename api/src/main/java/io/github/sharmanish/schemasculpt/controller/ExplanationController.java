package io.github.sharmanish.schemasculpt.controller;

import com.fasterxml.jackson.databind.ObjectMapper;
import io.github.sharmanish.schemasculpt.dto.ExplanationRequest;
import io.github.sharmanish.schemasculpt.dto.ExplanationResponse;
import io.github.sharmanish.schemasculpt.service.SessionService;
import io.github.sharmanish.schemasculpt.service.ai.AIService;
import io.github.sharmanish.schemasculpt.util.LogSanitizer;
import io.swagger.v3.oas.models.OpenAPI;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/explanations")
@CrossOrigin(origins = "*")
@Slf4j
public class ExplanationController {

  private final AIService aiService;
  private final SessionService sessionService;
  private final ObjectMapper objectMapper;

  public ExplanationController(
      AIService aiService, SessionService sessionService, ObjectMapper objectMapper) {
    this.aiService = aiService;
    this.sessionService = sessionService;
    this.objectMapper = objectMapper;
  }

  @PostMapping("/explain")
  public ResponseEntity<ExplanationResponse> explainValidationIssue(
      @RequestBody ExplanationRequest request, @RequestParam(required = false) String sessionId) {

    log.info(
        "Generating explanation for rule: {} in category: {}",
        LogSanitizer.sanitize(request.ruleId()),
        LogSanitizer.sanitize(request.category()));

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
          log.warn("Could not retrieve spec from session {}: {}", LogSanitizer.sanitize(sessionId), e.getMessage());
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
      ExplanationResponse response =
          new ExplanationResponse(
              (String) aiResponse.getOrDefault("explanation", "No explanation available"),
              (String) aiResponse.getOrDefault("severity", "info"),
              (String) aiResponse.getOrDefault("category", request.category()),
              (List<String>) aiResponse.getOrDefault("related_best_practices", List.of()),
              (List<String>) aiResponse.getOrDefault("example_solutions", List.of()),
              (List<String>) aiResponse.getOrDefault("additional_resources", List.of()),
              (Map<String, Object>) aiResponse.getOrDefault("metadata", Map.of()));

      log.info("Successfully generated explanation for rule: {}", LogSanitizer.sanitize(request.ruleId()));
      return ResponseEntity.ok(response);

    } catch (Exception e) {
      log.error(
          "Failed to generate explanation for rule {}: {}", LogSanitizer.sanitize(request.ruleId()), e.getMessage(), e);

      // Return a fallback explanation
      ExplanationResponse fallbackResponse =
          new ExplanationResponse(
              "An error occurred while generating the explanation. Please try again.",
              "error",
              request.category(),
              List.of(),
              List.of(),
              List.of(),
              Map.of("error", e.getMessage(), "rule_id", request.ruleId()));

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
