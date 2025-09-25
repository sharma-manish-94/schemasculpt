package io.github.sharma_manish_94.schemasculpt_api.service.ai;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.github.sharma_manish_94.schemasculpt_api.dto.ai.*;
import io.github.sharma_manish_94.schemasculpt_api.service.SessionService;
import io.github.sharma_manish_94.schemasculpt_api.service.SpecParsingService;
import io.swagger.v3.core.util.Json;
import io.swagger.v3.oas.models.OpenAPI;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.reactive.function.client.WebClientResponseException;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.UUID;

@Service
@Slf4j
public class EnhancedAIService {
    private final WebClient webClient;
    private final SessionService sessionService;
    private final SpecParsingService specParsingService;
    private final ObjectMapper objectMapper;

    public EnhancedAIService(WebClient.Builder webClientBuilder,
                           @Value("${ai.service.url}") String aiServiceUrl,
                           SessionService sessionService,
                           SpecParsingService specParsingService) {
        this.webClient = webClientBuilder
                .baseUrl(aiServiceUrl)
                .defaultHeader(HttpHeaders.CONTENT_TYPE, MediaType.APPLICATION_JSON_VALUE)
                .codecs(configurer -> configurer.defaultCodecs().maxInMemorySize(10 * 1024 * 1024)) // 10MB
                .build();
        this.sessionService = sessionService;
        this.specParsingService = specParsingService;
        this.objectMapper = new ObjectMapper();
    }

    // Enhanced AI Processing
    public Mono<EnhancedAIResponse> processSpecification(AIRequest request) {
        log.info("Processing enhanced AI request: operationType={}, streaming={}",
                 request.operationType(), request.streaming());

        return webClient.post()
                .uri("/ai/process")
                .bodyValue(request)
                .retrieve()
                .bodyToMono(AIServiceResponse.class)
                .map(AIServiceResponse::toEnhancedResponse)
                .timeout(Duration.ofMinutes(5))
                .onErrorResume(this::handleError);
    }

    // Streaming AI Processing
    public Flux<String> processSpecificationStreaming(AIRequest request) {
        log.info("Starting streaming AI processing for operationType={}", request.operationType());

        return webClient.post()
                .uri("/ai/process")
                .bodyValue(request.streaming() != StreamingMode.DISABLED ? request :
                          new AIRequest(request.specText(), request.prompt(), request.operationType(),
                                      request.sessionId(), request.userId(), StreamingMode.ENABLED,
                                      request.jsonPatches(), request.context(), request.responseFormat(),
                                      request.maxTokens(), request.temperature()))
                .accept(MediaType.TEXT_PLAIN)
                .retrieve()
                .bodyToFlux(String.class)
                .filter(chunk -> !chunk.equals("data: [DONE]"))
                .map(chunk -> chunk.startsWith("data: ") ? chunk.substring(6) : chunk)
                .timeout(Duration.ofMinutes(10))
                .onErrorResume(error -> {
                    log.error("Streaming error: {}", error.getMessage());
                    return Flux.just("{\"error\": \"Streaming failed: " + error.getMessage() + "\"}");
                });
    }

    // Agentic Specification Generation
    public Mono<EnhancedAIResponse> generateSpecification(GenerateSpecRequest request) {
        log.info("Generating specification for domain: {}, complexity: {}",
                 request.domain(), request.complexityLevel());

        return webClient.post()
                .uri("/ai/generate")
                .bodyValue(request)
                .retrieve()
                .bodyToMono(AIServiceResponse.class)
                .map(AIServiceResponse::toEnhancedResponse)
                .timeout(Duration.ofMinutes(10))
                .onErrorResume(this::handleError);
    }

    // Workflow Execution
    public Mono<WorkflowResponse> executeWorkflow(String workflowName, Map<String, Object> inputData) {
        log.info("Executing workflow: {}", workflowName);

        return webClient.post()
                .uri("/ai/workflow/{workflowName}", workflowName)
                .bodyValue(inputData)
                .retrieve()
                .bodyToMono(WorkflowResponse.class)
                .timeout(Duration.ofMinutes(15))
                .onErrorResume(error -> {
                    log.error("Workflow execution failed: {}", error.getMessage());
                    return Mono.just(WorkflowResponse.failed(workflowName, error.getMessage()));
                });
    }

    // Custom Workflow Execution
    public Mono<WorkflowResponse> executeCustomWorkflow(Map<String, Object> workflowDefinition) {
        log.info("Executing custom workflow: type={}",
                 workflowDefinition.get("workflow_type"));

        return webClient.post()
                .uri("/ai/workflow/custom")
                .bodyValue(workflowDefinition)
                .retrieve()
                .bodyToMono(WorkflowResponse.class)
                .timeout(Duration.ofMinutes(15))
                .onErrorResume(error -> {
                    log.error("Custom workflow execution failed: {}", error.getMessage());
                    return Mono.just(WorkflowResponse.failed("custom", error.getMessage()));
                });
    }

    // Get Available Workflows
    @SuppressWarnings("unchecked")
    public Mono<Map<String, Object>> getAvailableWorkflows() {
        return webClient.get()
                .uri("/ai/workflows")
                .retrieve()
                .bodyToMono(Map.class)
                .map(map -> (Map<String, Object>) map)
                .timeout(Duration.ofSeconds(30))
                .onErrorReturn(Map.of("workflows", List.of(), "error", "Failed to fetch workflows"));
    }

    // Context Management
    @SuppressWarnings("unchecked")
    public Mono<SessionContextResponse> createSession(String userId) {
        log.info("Creating AI context session for user: {}", userId);

        return webClient.post()
                .uri(uriBuilder -> uriBuilder.path("/ai/context/session")
                        .queryParamIfPresent("user_id", java.util.Optional.ofNullable(userId))
                        .build())
                .retrieve()
                .bodyToMono(Map.class)
                .map(rawMap -> (Map<String, Object>) rawMap)
                .map(response -> new SessionContextResponse(
                    (String) response.get("session_id"),
                    (String) response.get("user_id"),
                    parseInstant((String) response.get("created_at")),
                    parseInstant((String) response.get("created_at")), // Use created_at as last_activity initially
                    0,
                    Map.of("status", "created"),
                    List.of(),
                    Map.of()
                ))
                .timeout(Duration.ofSeconds(30))
                .onErrorReturn(new SessionContextResponse(UUID.randomUUID().toString(),
                                                        userId, Instant.now(), Instant.now(),
                                                        0, Map.of("status", "fallback"), List.of(), Map.of()));
    }

    // Get Session Summary
    @SuppressWarnings("unchecked")
    public Mono<SessionContextResponse> getSessionSummary(String sessionId) {
        return webClient.get()
                .uri("/ai/context/session/{sessionId}", sessionId)
                .retrieve()
                .bodyToMono(Map.class)
                .map(rawMap -> (Map<String, Object>) rawMap)
                .map(response -> {
                    Map<String, Object> summary = (Map<String, Object>) response.get("session_summary");
                    List<String> suggestions = (List<String>) response.get("suggestions");

                    return new SessionContextResponse(
                        sessionId,
                        (String) summary.get("user_id"),
                        Instant.now(),
                        Instant.now(),
                        (Integer) summary.getOrDefault("conversation_turns", 0),
                        summary,
                        suggestions != null ? suggestions : List.of(),
                        Map.of()
                    );
                })
                .timeout(Duration.ofSeconds(30))
                .onErrorReturn(new SessionContextResponse(sessionId, null, Instant.now(),
                                                        Instant.now(), 0, Map.of(), List.of(), Map.of()));
    }

    // Get Context Statistics
    @SuppressWarnings("unchecked")
    public Mono<Map<String, Object>> getContextStatistics() {
        return webClient.get()
                .uri("/ai/context/statistics")
                .retrieve()
                .bodyToMono(Map.class)
                .map(map -> (Map<String, Object>) map)
                .timeout(Duration.ofSeconds(30))
                .onErrorReturn(Map.of("error", "Failed to fetch statistics"));
    }

    // Prompt Generation
    @SuppressWarnings("unchecked")
    public Mono<Map<String, Object>> generateIntelligentPrompt(Map<String, Object> requestData, String contextId) {
        return webClient.post()
                .uri(uriBuilder -> uriBuilder.path("/ai/prompt/generate")
                        .queryParamIfPresent("context_id", java.util.Optional.ofNullable(contextId))
                        .build())
                .bodyValue(requestData)
                .retrieve()
                .bodyToMono(Map.class)
                .map(map -> (Map<String, Object>) map)
                .timeout(Duration.ofSeconds(30))
                .onErrorReturn(Map.of("error", "Failed to generate prompt"));
    }

    // Get Prompt Statistics
    @SuppressWarnings("unchecked")
    public Mono<Map<String, Object>> getPromptStatistics() {
        return webClient.get()
                .uri("/ai/prompt/statistics")
                .retrieve()
                .bodyToMono(Map.class)
                .map(map -> (Map<String, Object>) map)
                .timeout(Duration.ofSeconds(30))
                .onErrorReturn(Map.of("error", "Failed to fetch prompt statistics"));
    }

    // Agent Status
    @SuppressWarnings("unchecked")
    public Mono<Map<String, Object>> getAgentsStatus() {
        return webClient.get()
                .uri("/ai/agents/status")
                .retrieve()
                .bodyToMono(Map.class)
                .map(map -> (Map<String, Object>) map)
                .timeout(Duration.ofSeconds(30))
                .onErrorReturn(Map.of("status", "unavailable", "error", "Failed to fetch agent status"));
    }

    // Health Check
    public Mono<HealthResponse> healthCheck() {
        return webClient.get()
                .uri("/ai/health")
                .retrieve()
                .bodyToMono(HealthResponse.class)
                .timeout(Duration.ofSeconds(30))
                .onErrorReturn(HealthResponse.unhealthy("unknown"));
    }

    // Mock Server Operations
    public Mono<MockStartResponse> startMockServer(Map<String, Object> request) {
        log.info("Starting enhanced mock server");

        return webClient.post()
                .uri("/mock/start")
                .bodyValue(request)
                .retrieve()
                .bodyToMono(MockStartResponse.class)
                .timeout(Duration.ofMinutes(2))
                .onErrorResume(error -> {
                    log.error("Mock server start failed: {}", error.getMessage());
                    return Mono.error(new RuntimeException("Failed to start mock server: " + error.getMessage()));
                });
    }

    @SuppressWarnings("unchecked")
    public Mono<Map<String, Object>> updateMockServer(String mockId, Map<String, Object> request) {
        return webClient.put()
                .uri("/mock/{mockId}", mockId)
                .bodyValue(request)
                .retrieve()
                .bodyToMono(Map.class)
                .map(map -> (Map<String, Object>) map)
                .timeout(Duration.ofMinutes(2))
                .onErrorReturn(Map.of("error", "Failed to update mock server"));
    }

    @SuppressWarnings("unchecked")
    public Mono<Map<String, Object>> getMockServerInfo(String mockId) {
        return webClient.get()
                .uri("/mock/{mockId}", mockId)
                .retrieve()
                .bodyToMono(Map.class)
                .map(map -> (Map<String, Object>) map)
                .timeout(Duration.ofSeconds(30))
                .onErrorReturn(Map.of("error", "Mock server not found"));
    }

    // Session Integration Methods
    public Mono<EnhancedAIResponse> processSpecificationForSession(String sessionId, AIRequest request) {
        try {
            // Get current spec from session
            OpenAPI currentSpec = sessionService.getSpecForSession(sessionId);
            String specText = Json.pretty(currentSpec);

            // Update request with session spec
            AIRequest sessionRequest = new AIRequest(
                specText, request.prompt(), request.operationType(),
                sessionId, request.userId(), request.streaming(),
                request.jsonPatches(), request.context(), request.responseFormat(),
                request.maxTokens(), request.temperature()
            );

            return processSpecification(sessionRequest)
                    .doOnSuccess(response -> {
                        // Update session with new spec if successful
                        if (response.success() != null && response.success() && response.updatedSpecText() != null) {
                            try {
                                OpenAPI updatedSpec = specParsingService.parse(response.updatedSpecText()).getOpenAPI();
                                sessionService.updateSessionSpec(sessionId, updatedSpec);
                            } catch (Exception e) {
                                log.error("Failed to update session spec: {}", e.getMessage());
                            }
                        }
                    });
        } catch (Exception e) {
            log.error("Failed to process specification for session {}: {}", sessionId, e.getMessage());
            return Mono.just(EnhancedAIResponse.error(e.getMessage(), request.operationType()));
        }
    }

    // Error handling
    private Mono<EnhancedAIResponse> handleError(Throwable error) {
        log.error("AI service error: {}", error.getMessage());

        if (error instanceof WebClientResponseException webClientException) {
            String responseBody = webClientException.getResponseBodyAsString();
            log.error("AI service error response: {}", responseBody);

            try {
                Map<String, Object> errorResponse = objectMapper.readValue(responseBody, Map.class);
                String errorMessage = (String) errorResponse.getOrDefault("message", "Unknown error");
                return Mono.just(EnhancedAIResponse.error(errorMessage, OperationType.MODIFY));
            } catch (JsonProcessingException e) {
                return Mono.just(EnhancedAIResponse.error(webClientException.getMessage(), OperationType.MODIFY));
            }
        }

        return Mono.just(EnhancedAIResponse.error(error.getMessage(), OperationType.MODIFY));
    }

    // Helper method to parse timestamps from AI service
    private Instant parseInstant(String timestamp) {
        if (timestamp == null || timestamp.isEmpty()) {
            return Instant.now();
        }
        try {
            // Try parsing ISO format first
            return Instant.parse(timestamp);
        } catch (Exception e) {
            log.warn("Failed to parse timestamp '{}', using current time", timestamp);
            return Instant.now();
        }
    }
}