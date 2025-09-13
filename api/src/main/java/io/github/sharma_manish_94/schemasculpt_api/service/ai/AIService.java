package io.github.sharma_manish_94.schemasculpt_api.service.ai;

import com.fasterxml.jackson.core.JsonProcessingException;
import io.github.sharma_manish_94.schemasculpt_api.dto.AIRequest;
import io.github.sharma_manish_94.schemasculpt_api.dto.AIResponse;
import io.swagger.v3.core.util.Json;
import io.swagger.v3.core.util.Yaml;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

@Service
public class AIService {
	private final WebClient webClient;
	
	public AIService(WebClient.Builder webClientBuilder, @Value("${ai.service.url}") String aiServiceUrl) {
		this.webClient = WebClient.builder()
				                 .baseUrl(aiServiceUrl)
				                 .build();
	}
	
	public Mono<String> processSpecification(String specText, String userPrompt) {
		final AIRequest aiRequest = new AIRequest(specText, userPrompt);
		return this.webClient.post()
				       .uri("/process")
				       .contentType(MediaType.APPLICATION_JSON)
				       .bodyValue(aiRequest)
				       .retrieve()
				       .bodyToMono(AIResponse.class)
				       .map(aiResponse -> formatSpec(aiResponse.updatedSpecText()));
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
			// If formatting fails, return the raw text as a fallback
			return rawSpec;
		}
	}
}
