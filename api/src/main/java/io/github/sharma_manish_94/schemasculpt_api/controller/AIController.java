package io.github.sharma_manish_94.schemasculpt_api.controller;

import io.github.sharma_manish_94.schemasculpt_api.dto.AIRequest;
import io.github.sharma_manish_94.schemasculpt_api.dto.AIResponse;
import io.github.sharma_manish_94.schemasculpt_api.service.ai.AIService;
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Mono;

@RestController
@RequestMapping("/api/v1/ai")
public class AIController {
	private final AIService aiService;
	public AIController(AIService aiService) {
		this.aiService = aiService;
	}
	
	@PostMapping("/execute")
	public Mono<AIResponse> executeAiAction(@RequestBody AIRequest request) {
		return aiService.processSpecification(request.specText(),
				request.prompt())
				       .map(AIResponse::new);
	}
}
