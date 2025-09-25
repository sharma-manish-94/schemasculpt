package io.github.sharma_manish_94.schemasculpt_api.controller;

import io.github.sharma_manish_94.schemasculpt_api.service.ai.EnhancedAIService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.Duration;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/ai/prompt")
@RequiredArgsConstructor
@Slf4j
public class AIPromptController {
    private final EnhancedAIService enhancedAIService;

    @PostMapping("/generate")
    public ResponseEntity<Map<String, Object>> generateIntelligentPrompt(
            @RequestBody Map<String, Object> requestData,
            @RequestParam(required = false) String contextId) {
        log.info("Generating intelligent prompt with context: {}", contextId);

        try {
            Map<String, Object> response = enhancedAIService.generateIntelligentPrompt(requestData, contextId)
                    .timeout(Duration.ofSeconds(30))
                    .block();

            if (response == null) {
                response = Map.of(
                    "error", "No response from AI service",
                    "system_prompt", "",
                    "user_prompt", "",
                    "context_id", contextId != null ? contextId : ""
                );
            }

            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("Failed to generate intelligent prompt: {}", e.getMessage());

            Map<String, Object> errorResponse = Map.of(
                "error", e.getMessage(),
                "system_prompt", "",
                "user_prompt", "",
                "context_id", contextId != null ? contextId : ""
            );

            return ResponseEntity.ok(errorResponse);
        }
    }

    @GetMapping("/statistics")
    public ResponseEntity<Map<String, Object>> getPromptStatistics() {
        log.info("Fetching prompt engine statistics");

        try {
            Map<String, Object> statistics = enhancedAIService.getPromptStatistics()
                    .timeout(Duration.ofSeconds(30))
                    .block();

            if (statistics == null) {
                statistics = Map.of(
                    "status", "unavailable",
                    "total_prompts_generated", 0,
                    "average_prompt_length", 0,
                    "most_used_templates", "[]"
                );
            }

            return ResponseEntity.ok(statistics);
        } catch (Exception e) {
            log.error("Failed to fetch prompt statistics: {}", e.getMessage());

            Map<String, Object> errorResponse = Map.of(
                "status", "error",
                "error_message", e.getMessage(),
                "total_prompts_generated", 0,
                "average_prompt_length", 0
            );

            return ResponseEntity.ok(errorResponse);
        }
    }

    @PostMapping("/template/{templateName}")
    public ResponseEntity<Map<String, Object>> usePromptTemplate(
            @PathVariable String templateName,
            @RequestBody Map<String, Object> templateVariables) {
        log.info("Using prompt template: {}", templateName);

        // Since the AI service doesn't expose template endpoints directly,
        // we'll create a structured request for prompt generation
        Map<String, Object> requestData = Map.of(
            "template_name", templateName,
            "template_variables", templateVariables,
            "operation_type", "template"
        );

        try {
            Map<String, Object> response = enhancedAIService.generateIntelligentPrompt(requestData, null)
                    .timeout(Duration.ofSeconds(30))
                    .block();

            if (response == null) {
                response = Map.of(
                    "error", "Template not found or AI service unavailable",
                    "template_name", templateName,
                    "generated_prompt", ""
                );
            } else {
                // Enhance response with template information
                response = Map.of(
                    "template_name", templateName,
                    "generated_prompt", response.getOrDefault("user_prompt", ""),
                    "system_prompt", response.getOrDefault("system_prompt", ""),
                    "variables_used", templateVariables
                );
            }

            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("Failed to use prompt template {}: {}", templateName, e.getMessage());

            Map<String, Object> errorResponse = Map.of(
                "error", e.getMessage(),
                "template_name", templateName,
                "generated_prompt", ""
            );

            return ResponseEntity.ok(errorResponse);
        }
    }

    @GetMapping("/templates")
    public ResponseEntity<Map<String, Object>> getAvailableTemplates() {
        log.info("Fetching available prompt templates");

        // Since the AI service doesn't expose a templates endpoint,
        // we'll return a predefined list of common templates
        Map<String, Object> templates = Map.of(
            "templates", Map.of(
                "specification_enhancement", Map.of(
                    "name", "Specification Enhancement",
                    "description", "Enhances OpenAPI specifications with better descriptions and examples",
                    "variables", new String[]{"spec_text", "enhancement_type"}
                ),
                "mock_data_generation", Map.of(
                    "name", "Mock Data Generation",
                    "description", "Generates realistic mock data based on schema definitions",
                    "variables", new String[]{"schema", "data_type", "count"}
                ),
                "api_documentation", Map.of(
                    "name", "API Documentation",
                    "description", "Improves API documentation and adds comprehensive descriptions",
                    "variables", new String[]{"spec_text", "documentation_style"}
                ),
                "validation_rules", Map.of(
                    "name", "Validation Rules",
                    "description", "Adds validation rules and constraints to schema definitions",
                    "variables", new String[]{"schema", "validation_type"}
                )
            ),
            "total_templates", 4,
            "status", "available"
        );

        return ResponseEntity.ok(templates);
    }

    @PostMapping("/optimize")
    public ResponseEntity<Map<String, Object>> optimizePrompt(@RequestBody Map<String, Object> promptData) {
        log.info("Optimizing prompt for better AI performance");

        String originalPrompt = (String) promptData.getOrDefault("prompt", "");
        String operationType = (String) promptData.getOrDefault("operation_type", "modify");

        // Create an optimization request
        Map<String, Object> requestData = Map.of(
            "prompt", originalPrompt,
            "operation_type", "optimize",
            "optimization_goal", promptData.getOrDefault("goal", "clarity")
        );

        try {
            Map<String, Object> response = enhancedAIService.generateIntelligentPrompt(requestData, null)
                    .timeout(Duration.ofSeconds(30))
                    .block();

            if (response == null) {
                response = Map.of(
                    "error", "Prompt optimization failed",
                    "original_prompt", originalPrompt,
                    "optimized_prompt", originalPrompt
                );
            } else {
                response = Map.of(
                    "original_prompt", originalPrompt,
                    "optimized_prompt", response.getOrDefault("user_prompt", originalPrompt),
                    "optimization_notes", response.getOrDefault("system_prompt", ""),
                    "improvement_score", calculateImprovementScore(originalPrompt, (String) response.get("user_prompt"))
                );
            }

            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("Failed to optimize prompt: {}", e.getMessage());

            Map<String, Object> errorResponse = Map.of(
                "error", e.getMessage(),
                "original_prompt", originalPrompt,
                "optimized_prompt", originalPrompt
            );

            return ResponseEntity.ok(errorResponse);
        }
    }

    private double calculateImprovementScore(String original, String optimized) {
        if (original == null || optimized == null) {
            return 0.0;
        }

        // Simple scoring based on length and complexity improvements
        double lengthImprovement = Math.min(2.0, (double) optimized.length() / original.length());
        double complexityScore = optimized.split("\\W+").length > original.split("\\W+").length ? 1.2 : 1.0;

        return Math.min(10.0, lengthImprovement * complexityScore * 5.0);
    }
}