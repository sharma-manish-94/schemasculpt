package io.github.sharma_manish_94.schemasculpt_api.service.ai;

import com.fasterxml.jackson.core.JsonProcessingException;
import io.github.sharma_manish_94.schemasculpt_api.dto.AIProxyRequest;
import io.github.sharma_manish_94.schemasculpt_api.dto.AIResponse;
import io.github.sharma_manish_94.schemasculpt_api.service.SessionService;
import io.github.sharma_manish_94.schemasculpt_api.service.SpecParsingService;
import io.swagger.v3.core.util.Json;
import io.swagger.v3.core.util.Yaml;
import io.swagger.v3.oas.models.OpenAPI;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;

@Service
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
        OpenAPI openApi = sessionService.getSpecForSession(sessionId);
        String specText = Json.pretty(openApi);

        AIProxyRequest aiRequest = new AIProxyRequest(specText, userPrompt);

        String updatedSpecText = callAIService(aiRequest);
        System.out.println(updatedSpecText);
        OpenAPI updatedOpenApi = specParsingService.parse(updatedSpecText).getOpenAPI();
        // Save the new version back to the Redis session
        sessionService.updateSessionSpec(sessionId, updatedOpenApi);
        // Return the new object
        return updatedSpecText;
    }

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
