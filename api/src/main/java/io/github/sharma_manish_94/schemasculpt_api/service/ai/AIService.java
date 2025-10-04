package io.github.sharma_manish_94.schemasculpt_api.service.ai;

import com.fasterxml.jackson.core.JsonProcessingException;
import org.springframework.core.ParameterizedTypeReference;
import io.github.sharma_manish_94.schemasculpt_api.dto.AIMetaAnalysisRequest;
import io.github.sharma_manish_94.schemasculpt_api.dto.AIMetaAnalysisResponse;
import io.github.sharma_manish_94.schemasculpt_api.dto.AIProxyRequest;
import io.github.sharma_manish_94.schemasculpt_api.dto.AIResponse;
import io.github.sharma_manish_94.schemasculpt_api.dto.ai.SmartAIFixRequest;
import io.github.sharma_manish_94.schemasculpt_api.dto.ai.SmartAIFixResponse;
import io.github.sharma_manish_94.schemasculpt_api.service.SessionService;
import io.github.sharma_manish_94.schemasculpt_api.service.SpecParsingService;
import io.swagger.v3.core.util.Json;
import io.swagger.v3.core.util.Yaml;
import io.swagger.v3.oas.models.OpenAPI;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;

import java.util.Map;

@Service
@Slf4j
public class AIService {
    private final WebClient webClient;
    private final SessionService sessionService;
    private final SpecParsingService specParsingService;

    public AIService(WebClient.Builder webClientBuilder, @Value("${ai.service.url}") String aiServiceUrl, SessionService sessionService, SpecParsingService specParsingService) {
        this.webClient = webClientBuilder.baseUrl(aiServiceUrl).build();
        this.sessionService = sessionService;
        this.specParsingService = specParsingService;
    }

    public String processSpecification(String sessionId, String userPrompt) {
        log.info("Processing AI request for sessionId: {}", sessionId);
        OpenAPI openApi = sessionService.getSpecForSession(sessionId);
        String specText = Json.pretty(openApi);

        // Use smart fix endpoint for optimized processing
        SmartAIFixRequest smartRequest = new SmartAIFixRequest(specText, userPrompt);
        String updatedSpecText = callSmartAIFix(smartRequest);

        OpenAPI updatedOpenApi = specParsingService.parse(updatedSpecText).getOpenAPI();
        sessionService.updateSessionSpec(sessionId, updatedOpenApi);
        return updatedSpecText;
    }

    /**
     * Call the optimized smart AI fix endpoint.
     * This endpoint intelligently chooses between JSON patches (fast, targeted)
     * and full regeneration (slow, broad changes) based on the prompt.
     */
    private String callSmartAIFix(SmartAIFixRequest request) {
        log.info("Calling smart AI fix endpoint");

        try {
            SmartAIFixResponse response = this.webClient.post()
                    .uri("/ai/fix/smart")
                    .contentType(MediaType.APPLICATION_JSON)
                    .bodyValue(request)
                    .retrieve()
                    .bodyToMono(SmartAIFixResponse.class)
                    .block();

            if (response != null && response.updatedSpecText() != null) {
                log.info("Smart AI fix completed using {} method in {}ms ({} tokens)",
                        response.methodUsed(),
                        response.processingTimeMs(),
                        response.tokenCount());
                return formatSpec(response.updatedSpecText());
            } else {
                log.warn("Smart AI fix returned null or empty response, response: {}", response);
                throw new RuntimeException("AI service returned invalid response");
            }
        } catch (Exception e) {
            log.error("Smart AI fix failed, falling back to legacy endpoint: {}", e.getMessage());
            // Fallback to legacy endpoint if smart fix fails
            AIProxyRequest legacyRequest = new AIProxyRequest(request.specText(), request.prompt());
            return callAIService(legacyRequest);
        }
    }

    /**
     * Legacy method: Call the original /process endpoint for full regeneration.
     * Kept for backward compatibility, but prefer callSmartAIFix() for better performance.
     */
    @Deprecated
    private String callAIService(AIProxyRequest aiRequest) {
        return this.webClient.post()
                .uri("/process")
                .contentType(MediaType.APPLICATION_JSON)
                .bodyValue(aiRequest)
                .retrieve()
                .bodyToMono(AIResponse.class)
                .map(AIResponse::updatedSpecText)
                .map(this::formatSpec)
                .block();
    }

    public String processSpecification(OpenAPI openApi, String userPrompt) {
        String specText = Json.pretty(openApi);
        AIProxyRequest aiRequest = new AIProxyRequest(specText, userPrompt);
        return callAIService(aiRequest);
    }

    public Map<String, Object> explainValidationIssue(Map<String, Object> request) {
        log.info("Requesting explanation for validation issue");

        try {
            return this.webClient.post()
                    .uri("/ai/explain")
                    .contentType(MediaType.APPLICATION_JSON)
                    .bodyValue(request)
                    .retrieve()
                    .bodyToMono(new ParameterizedTypeReference<Map<String, Object>>() {})
                    .block();
        } catch (Exception e) {
            log.error("Failed to get explanation from AI service: {}", e.getMessage(), e);
            throw new RuntimeException("AI explanation service unavailable", e);
        }
    }

    public Map<String, Object> generateTestCases(Map<String, Object> request) {
        log.info("Requesting test case generation for operation: {}",
                request.get("operation_summary"));

        try {
            return this.webClient.post()
                    .uri("/ai/test-cases/generate")
                    .contentType(MediaType.APPLICATION_JSON)
                    .bodyValue(request)
                    .retrieve()
                    .bodyToMono(new ParameterizedTypeReference<Map<String, Object>>() {})
                    .block();
        } catch (Exception e) {
            log.error("Failed to generate test cases from AI service: {}", e.getMessage(), e);
            throw new RuntimeException("AI test generation service unavailable", e);
        }
    }

    public Map<String, Object> generateTestSuite(Map<String, Object> request) {
        log.info("Requesting complete test suite generation");

        try {
            return this.webClient.post()
                    .uri("/ai/test-suite/generate")
                    .contentType(MediaType.APPLICATION_JSON)
                    .bodyValue(request)
                    .retrieve()
                    .bodyToMono(new ParameterizedTypeReference<Map<String, Object>>() {})
                    .block();
        } catch (Exception e) {
            log.error("Failed to generate test suite from AI service: {}", e.getMessage(), e);
            throw new RuntimeException("AI test suite generation service unavailable", e);
        }
    }

    /**
     * Perform AI meta-analysis on linter findings to detect higher-order patterns,
     * security threats, and design issues.
     */
    public AIMetaAnalysisResponse performMetaAnalysis(AIMetaAnalysisRequest request) {
        log.info("Requesting AI meta-analysis with {} errors and {} suggestions",
                request.errors().size(), request.suggestions().size());

        try {
            AIMetaAnalysisResponse response = this.webClient.post()
                    .uri("/ai/meta-analysis")
                    .contentType(MediaType.APPLICATION_JSON)
                    .bodyValue(request)
                    .retrieve()
                    .bodyToMono(AIMetaAnalysisResponse.class)
                    .block();

            if (response != null) {
                log.info("Meta-analysis completed with {} insights (confidence: {})",
                        response.insights().size(), response.confidenceScore());
                return response;
            } else {
                log.warn("Meta-analysis returned null response");
                throw new RuntimeException("AI meta-analysis service returned invalid response");
            }
        } catch (Exception e) {
            log.error("Failed to perform AI meta-analysis: {}", e.getMessage(), e);
            throw new RuntimeException("AI meta-analysis service unavailable", e);
        }
    }

    private String formatSpec(String rawSpec) {
        if (rawSpec == null || rawSpec.isBlank()) {
            return "";
        }
        try {
            // Heuristic to detect if the string is JSON
            if (rawSpec.trim().startsWith("{")) {
                Object jsonObject = Json.mapper().readValue(rawSpec, Object.class);
                return Json.pretty(jsonObject);
            } else {
                Object yamlObject = Yaml.mapper().readValue(rawSpec, Object.class);
                return Yaml.pretty(yamlObject);
            }
        } catch (JsonProcessingException e) {
            return rawSpec;
        }
    }
}
