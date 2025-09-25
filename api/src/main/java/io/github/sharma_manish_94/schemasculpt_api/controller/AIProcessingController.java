package io.github.sharma_manish_94.schemasculpt_api.controller;

import io.github.sharma_manish_94.schemasculpt_api.dto.ai.*;
import io.github.sharma_manish_94.schemasculpt_api.service.ai.EnhancedAIService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;
import reactor.core.publisher.Flux;

import java.io.IOException;
import java.time.Duration;
import java.util.Map;
import java.util.concurrent.CompletableFuture;

@RestController
@RequestMapping("/api/v1/ai")
@RequiredArgsConstructor
@Slf4j
public class AIProcessingController {
    private final EnhancedAIService enhancedAIService;

    @PostMapping("/process")
    public ResponseEntity<?> processSpecification(@RequestBody AIRequest request) {
        log.info("Processing AI request: operationType={}, streaming={}",
                 request.operationType(), request.streaming());

        // Handle streaming requests
        if (request.streaming() != null && request.streaming() != StreamingMode.DISABLED) {
            return processSpecificationStreaming(request);
        }

        // Handle regular requests
        try {
            EnhancedAIResponse response = enhancedAIService.processSpecification(request)
                    .timeout(Duration.ofMinutes(5))
                    .block();

            if (response == null) {
                return ResponseEntity.internalServerError()
                        .body(EnhancedAIResponse.error("No response from AI service", request.operationType()));
            }

            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("AI processing failed: {}", e.getMessage());
            return ResponseEntity.internalServerError()
                    .body(EnhancedAIResponse.error(e.getMessage(), request.operationType()));
        }
    }

    @PostMapping(value = "/process/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public ResponseEntity<SseEmitter> processSpecificationStreaming(@RequestBody AIRequest request) {
        log.info("Starting streaming AI processing for operationType={}", request.operationType());

        SseEmitter emitter = new SseEmitter(Duration.ofMinutes(10).toMillis());

        CompletableFuture.runAsync(() -> {
            try {
                Flux<String> streamFlux = enhancedAIService.processSpecificationStreaming(request);

                streamFlux
                        .doOnNext(chunk -> {
                            try {
                                emitter.send(SseEmitter.event()
                                        .name("chunk")
                                        .data(chunk));
                            } catch (IOException e) {
                                log.error("Error sending SSE chunk: {}", e.getMessage());
                                emitter.completeWithError(e);
                            }
                        })
                        .doOnComplete(() -> {
                            try {
                                emitter.send(SseEmitter.event()
                                        .name("complete")
                                        .data("Stream completed"));
                                emitter.complete();
                            } catch (IOException e) {
                                log.error("Error completing SSE: {}", e.getMessage());
                                emitter.completeWithError(e);
                            }
                        })
                        .doOnError(error -> {
                            log.error("Streaming error: {}", error.getMessage());
                            emitter.completeWithError(error);
                        })
                        .subscribe();

            } catch (Exception e) {
                log.error("Error setting up stream: {}", e.getMessage());
                emitter.completeWithError(e);
            }
        });

        emitter.onCompletion(() -> log.info("SSE connection completed"));
        emitter.onTimeout(() -> log.warn("SSE connection timed out"));
        emitter.onError(throwable -> log.error("SSE error: {}", throwable.getMessage()));

        return ResponseEntity.ok(emitter);
    }

    @PostMapping("/generate")
    public ResponseEntity<EnhancedAIResponse> generateSpecification(@RequestBody GenerateSpecRequest request) {
        log.info("Generating specification for domain: {}, complexity: {}",
                 request.domain(), request.complexityLevel());

        try {
            EnhancedAIResponse response = enhancedAIService.generateSpecification(request)
                    .timeout(Duration.ofMinutes(10))
                    .block();

            if (response == null) {
                return ResponseEntity.internalServerError()
                        .body(EnhancedAIResponse.error("No response from AI service", OperationType.GENERATE));
            }

            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("Specification generation failed: {}", e.getMessage());
            return ResponseEntity.internalServerError()
                    .body(EnhancedAIResponse.error(e.getMessage(), OperationType.GENERATE));
        }
    }

    @PostMapping("/workflow/{workflowName}")
    public ResponseEntity<WorkflowResponse> executeWorkflow(
            @PathVariable String workflowName,
            @RequestBody Map<String, Object> inputData) {
        log.info("Executing workflow: {}", workflowName);

        try {
            WorkflowResponse response = enhancedAIService.executeWorkflow(workflowName, inputData)
                    .timeout(Duration.ofMinutes(15))
                    .block();

            if (response == null) {
                return ResponseEntity.internalServerError()
                        .body(WorkflowResponse.failed(workflowName, "No response from AI service"));
            }

            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("Workflow execution failed: {}", e.getMessage());
            return ResponseEntity.internalServerError()
                    .body(WorkflowResponse.failed(workflowName, e.getMessage()));
        }
    }

    @PostMapping("/workflow/custom")
    public ResponseEntity<WorkflowResponse> executeCustomWorkflow(
            @RequestBody Map<String, Object> workflowDefinition) {
        String workflowType = (String) workflowDefinition.getOrDefault("workflow_type", "custom");
        log.info("Executing custom workflow: type={}", workflowType);

        try {
            WorkflowResponse response = enhancedAIService.executeCustomWorkflow(workflowDefinition)
                    .timeout(Duration.ofMinutes(15))
                    .block();

            if (response == null) {
                return ResponseEntity.internalServerError()
                        .body(WorkflowResponse.failed("custom", "No response from AI service"));
            }

            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("Custom workflow execution failed: {}", e.getMessage());
            return ResponseEntity.internalServerError()
                    .body(WorkflowResponse.failed("custom", e.getMessage()));
        }
    }

    @GetMapping("/workflows")
    public ResponseEntity<Map<String, Object>> getAvailableWorkflows() {
        log.info("Fetching available workflows");

        try {
            Map<String, Object> workflows = enhancedAIService.getAvailableWorkflows()
                    .timeout(Duration.ofSeconds(30))
                    .block();

            return ResponseEntity.ok(workflows != null ? workflows : Map.of("workflows", "[]"));
        } catch (Exception e) {
            log.error("Failed to fetch workflows: {}", e.getMessage());
            return ResponseEntity.ok(Map.of("error", e.getMessage(), "workflows", "[]"));
        }
    }

    @GetMapping("/health")
    public ResponseEntity<HealthResponse> healthCheck() {
        log.info("Performing AI health check");

        try {
            HealthResponse response = enhancedAIService.healthCheck()
                    .timeout(Duration.ofSeconds(30))
                    .block();

            return ResponseEntity.ok(response != null ? response : HealthResponse.unhealthy("unknown"));
        } catch (Exception e) {
            log.error("AI health check failed: {}", e.getMessage());
            return ResponseEntity.ok(HealthResponse.unhealthy("unknown"));
        }
    }
}