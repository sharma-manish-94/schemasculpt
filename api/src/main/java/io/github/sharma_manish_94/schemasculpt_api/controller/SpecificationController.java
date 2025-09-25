package io.github.sharma_manish_94.schemasculpt_api.controller;

import io.github.sharma_manish_94.schemasculpt_api.dto.AIProxyRequest;
import io.github.sharma_manish_94.schemasculpt_api.dto.QuickFixRequest;
import io.github.sharma_manish_94.schemasculpt_api.dto.ValidationResult;
import io.github.sharma_manish_94.schemasculpt_api.dto.ai.*;
import io.github.sharma_manish_94.schemasculpt_api.service.SessionService;
import io.github.sharma_manish_94.schemasculpt_api.service.ValidationService;
import io.github.sharma_manish_94.schemasculpt_api.service.ai.AIService;
import io.github.sharma_manish_94.schemasculpt_api.service.ai.EnhancedAIService;
import io.github.sharma_manish_94.schemasculpt_api.service.fix.QuickFixService;
import io.swagger.v3.core.util.Json;
import io.swagger.v3.oas.models.OpenAPI;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.Duration;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/sessions/{sessionId}/spec")
@Slf4j
public class SpecificationController {
    private final SessionService sessionService;
    private final ValidationService validationService;
    private final QuickFixService quickFixService;
    private final AIService aiService;
    private final EnhancedAIService enhancedAIService;

    public SpecificationController(final SessionService sessionService,
                                   final ValidationService validationService,
                                   final QuickFixService quickFixService,
                                   final AIService aiService,
                                   final EnhancedAIService enhancedAIService) {
        this.sessionService = sessionService;
        this.validationService = validationService;
        this.quickFixService = quickFixService;
        this.aiService = aiService;
        this.enhancedAIService = enhancedAIService;
    }

    @PostMapping("/validate")
    public ResponseEntity<ValidationResult> validateSpecification(@PathVariable String sessionId) {
        OpenAPI openAPI = sessionService.getSpecForSession(sessionId);
        ValidationResult validationResult = validationService.analyze(openAPI);
        return ResponseEntity.ok(validationResult);
    }

    @PostMapping("/fix")
    public ResponseEntity<OpenAPI> applyQuickFix(
            @PathVariable String sessionId,
            @RequestBody QuickFixRequest quickFixRequest) {
        OpenAPI updatedSpec = quickFixService.applyFix(sessionId, quickFixRequest);
        return ResponseEntity.ok(updatedSpec);
    }

    @PostMapping("/transform")
    public ResponseEntity<OpenAPI> executeAIAction(
            @PathVariable String sessionId,
            @RequestBody AIProxyRequest request) {
        aiService.processSpecification(sessionId, request.prompt());
        OpenAPI updatedSpecObject = sessionService.getSpecForSession(sessionId);
        return ResponseEntity.ok(updatedSpecObject);
    }

    // Enhanced AI Processing Methods

    @PostMapping("/ai/process-advanced")
    public ResponseEntity<EnhancedAIResponse> processAdvancedAI(
            @PathVariable String sessionId,
            @RequestBody AIRequest request) {
        log.info("Processing advanced AI request for session: {}, operation: {}",
                 sessionId, request.operationType());

        try {
            EnhancedAIResponse response = enhancedAIService.processSpecificationForSession(sessionId, request)
                    .timeout(Duration.ofMinutes(5))
                    .block();

            if (response == null) {
                return ResponseEntity.internalServerError()
                        .body(EnhancedAIResponse.error("No response from AI service", request.operationType()));
            }

            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("Advanced AI processing failed for session {}: {}", sessionId, e.getMessage());
            return ResponseEntity.internalServerError()
                    .body(EnhancedAIResponse.error(e.getMessage(), request.operationType()));
        }
    }

    @PostMapping("/ai/generate-spec")
    public ResponseEntity<EnhancedAIResponse> generateSpecification(
            @PathVariable String sessionId,
            @RequestBody GenerateSpecRequest request) {
        log.info("Generating specification for session: {}, domain: {}",
                 sessionId, request.domain());

        try {
            // Add session context to the request
            GenerateSpecRequest sessionRequest = new GenerateSpecRequest(
                request.domain(),
                request.description(),
                request.apiType(),
                request.complexityLevel(),
                request.includeExamples(),
                request.authenticationType(),
                request.additionalRequirements(),
                request.streaming(),
                request.userId(),
                sessionId, // Use the session ID
                request.customSchemas(),
                request.targetVersion()
            );

            EnhancedAIResponse response = enhancedAIService.generateSpecification(sessionRequest)
                    .timeout(Duration.ofMinutes(10))
                    .block();

            if (response == null) {
                return ResponseEntity.internalServerError()
                        .body(EnhancedAIResponse.error("No response from AI service", OperationType.GENERATE));
            }

            // Update session with generated spec if successful
            if (response.success() != null && response.success() && response.updatedSpecText() != null) {
                try {
                    // Parse and update the session
                    OpenAPI generatedSpec = Json.mapper().readValue(response.updatedSpecText(), OpenAPI.class);
                    sessionService.updateSessionSpec(sessionId, generatedSpec);
                } catch (Exception e) {
                    log.warn("Failed to update session with generated spec: {}", e.getMessage());
                }
            }

            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("Specification generation failed for session {}: {}", sessionId, e.getMessage());
            return ResponseEntity.internalServerError()
                    .body(EnhancedAIResponse.error(e.getMessage(), OperationType.GENERATE));
        }
    }

    @PostMapping("/ai/workflow/{workflowName}")
    public ResponseEntity<WorkflowResponse> executeSessionWorkflow(
            @PathVariable String sessionId,
            @PathVariable String workflowName,
            @RequestBody Map<String, Object> inputData) {
        log.info("Executing workflow {} for session: {}", workflowName, sessionId);

        try {
            // Add session context to input data
            OpenAPI currentSpec = sessionService.getSpecForSession(sessionId);
            String specText = Json.pretty(currentSpec);

            Map<String, Object> sessionInputData = Map.of(
                "session_id", sessionId,
                "spec_text", specText,
                "workflow_input", inputData
            );

            WorkflowResponse response = enhancedAIService.executeWorkflow(workflowName, sessionInputData)
                    .timeout(Duration.ofMinutes(15))
                    .block();

            if (response == null) {
                return ResponseEntity.internalServerError()
                        .body(WorkflowResponse.failed(workflowName, "No response from AI service"));
            }

            // Update session if workflow produced a new spec
            if ("completed".equals(response.status()) && response.result() instanceof Map) {
                Map<String, Object> result = (Map<String, Object>) response.result();
                if (result.containsKey("updated_spec_text")) {
                    try {
                        String updatedSpec = (String) result.get("updated_spec_text");
                        OpenAPI newSpec = Json.mapper().readValue(updatedSpec, OpenAPI.class);
                        sessionService.updateSessionSpec(sessionId, newSpec);
                    } catch (Exception e) {
                        log.warn("Failed to update session with workflow result: {}", e.getMessage());
                    }
                }
            }

            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("Workflow execution failed for session {}: {}", sessionId, e.getMessage());
            return ResponseEntity.internalServerError()
                    .body(WorkflowResponse.failed(workflowName, e.getMessage()));
        }
    }

    @PostMapping("/ai/analyze")
    public ResponseEntity<Map<String, Object>> analyzeSpecification(@PathVariable String sessionId) {
        log.info("Analyzing specification for session: {}", sessionId);

        try {
            OpenAPI currentSpec = sessionService.getSpecForSession(sessionId);
            String specText = Json.pretty(currentSpec);

            AIRequest analysisRequest = new AIRequest(
                specText,
                "Analyze this OpenAPI specification and provide insights on its structure, completeness, and potential improvements.",
                OperationType.ANALYZE,
                sessionId,
                null,
                StreamingMode.DISABLED,
                null,
                null,
                null,
                null,
                null
            );

            EnhancedAIResponse response = enhancedAIService.processSpecification(analysisRequest)
                    .timeout(Duration.ofMinutes(3))
                    .block();

            if (response == null) {
                return ResponseEntity.ok(Map.of(
                    "error", "Analysis failed - no response from AI service",
                    "session_id", sessionId
                ));
            }

            Map<String, Object> analysisResult = Map.of(
                "session_id", sessionId,
                "analysis", response.updatedSpecText(),
                "operation_successful", response.success() != null ? response.success() : false,
                "suggestions", response.suggestions() != null ? response.suggestions() : "[]",
                "processing_time_ms", response.processingTimeMs() != null ? response.processingTimeMs() : 0
            );

            return ResponseEntity.ok(analysisResult);
        } catch (Exception e) {
            log.error("Specification analysis failed for session {}: {}", sessionId, e.getMessage());

            return ResponseEntity.ok(Map.of(
                "error", e.getMessage(),
                "session_id", sessionId,
                "analysis", "Analysis failed due to an error"
            ));
        }
    }

    @PostMapping("/ai/optimize")
    public ResponseEntity<EnhancedAIResponse> optimizeSpecification(
            @PathVariable String sessionId,
            @RequestBody(required = false) Map<String, Object> optimizationOptions) {
        log.info("Optimizing specification for session: {}", sessionId);

        try {
            OpenAPI currentSpec = sessionService.getSpecForSession(sessionId);
            String specText = Json.pretty(currentSpec);

            String optimizationPrompt = buildOptimizationPrompt(optimizationOptions);

            AIRequest optimizationRequest = new AIRequest(
                specText,
                optimizationPrompt,
                OperationType.OPTIMIZE,
                sessionId,
                null,
                StreamingMode.DISABLED,
                null,
                optimizationOptions,
                null,
                null,
                null
            );

            EnhancedAIResponse response = enhancedAIService.processSpecificationForSession(sessionId, optimizationRequest)
                    .timeout(Duration.ofMinutes(5))
                    .block();

            if (response == null) {
                return ResponseEntity.internalServerError()
                        .body(EnhancedAIResponse.error("Optimization failed - no response from AI service", OperationType.OPTIMIZE));
            }

            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("Specification optimization failed for session {}: {}", sessionId, e.getMessage());
            return ResponseEntity.internalServerError()
                    .body(EnhancedAIResponse.error(e.getMessage(), OperationType.OPTIMIZE));
        }
    }

    // Helper method to build optimization prompt
    private String buildOptimizationPrompt(Map<String, Object> options) {
        if (options == null || options.isEmpty()) {
            return "Optimize this OpenAPI specification for better structure, clarity, and completeness. Add missing descriptions, improve naming conventions, and ensure best practices are followed.";
        }

        StringBuilder prompt = new StringBuilder("Optimize this OpenAPI specification with focus on: ");

        if (options.containsKey("focus_areas")) {
            prompt.append(String.join(", ", (String[]) options.get("focus_areas")));
        } else {
            prompt.append("general improvements");
        }

        if (options.containsKey("target_audience")) {
            prompt.append(". Target audience: ").append(options.get("target_audience"));
        }

        if (options.containsKey("compliance_standards")) {
            prompt.append(". Ensure compliance with: ").append(String.join(", ", (String[]) options.get("compliance_standards")));
        }

        return prompt.toString();
    }
}
