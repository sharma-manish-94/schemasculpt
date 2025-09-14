package io.github.sharma_manish_94.schemasculpt_api.controller;

import io.github.sharma_manish_94.schemasculpt_api.dto.MockStartRequest;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

@RestController
@RequestMapping("/api/v1/mock")
@CrossOrigin(origins = "${app.cors.allowed-origins}")
public class MockController {
	
	private final WebClient webClient;
	
	public MockController(WebClient.Builder webClientBuilder, @Value("${ai.service.url}") String aiServiceUrl) {
		this.webClient = webClientBuilder.baseUrl(aiServiceUrl).build();
	}
	
	@PostMapping("/start")
	public Mono<ResponseEntity<String>> startMockServer(@RequestBody MockStartRequest request) {
		return this.webClient.post()
				       .uri("/mock/start")
				       .contentType(MediaType.APPLICATION_JSON)
				       .bodyValue(request)
				       .retrieve()
				       .toEntity(String.class); // Forward the raw response
	}
	
	@PutMapping("/{mockId}")
	public Mono<ResponseEntity<String>> updateMockServer(
			@PathVariable String mockId,
			@RequestBody MockStartRequest request) {
		
		return this.webClient.put()
				       .uri("/mock/" + mockId)
				       .contentType(MediaType.APPLICATION_JSON)
				       .bodyValue(request)
				       .retrieve()
				       .toEntity(String.class);
	}
}
