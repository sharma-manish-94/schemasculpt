package io.github.sharma_manish_94.schemasculpt_api.controller;

import io.github.sharma_manish_94.schemasculpt_api.dto.MockSessionDetails;
import io.github.sharma_manish_94.schemasculpt_api.dto.MockSessionResponse;
import io.github.sharma_manish_94.schemasculpt_api.dto.MockStartRequest;
import io.github.sharma_manish_94.schemasculpt_api.dto.SessionResponse;
import io.github.sharma_manish_94.schemasculpt_api.service.SessionService;
import io.swagger.v3.core.util.Yaml;
import io.swagger.v3.oas.models.OpenAPI;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

import java.util.Objects;

@RestController
@RequestMapping("/api/v1/sessions")
public class SessionController {
    private final SessionService sessionService;
    private final WebClient webClient;

    public SessionController(
            final SessionService sessionService,
            final WebClient.Builder webClientBuilder,
            @Value("${ai.service.url}") String aiServiceUrl) {
        this.sessionService = sessionService;
        this.webClient = webClientBuilder.baseUrl(aiServiceUrl).build();
    }

    @PostMapping
    public ResponseEntity<SessionResponse> createSession(@RequestBody String specText) {
        String sessionId = sessionService.createSession(specText);
        return ResponseEntity.ok(new SessionResponse(sessionId));
    }

    @PostMapping("/mock")
    public Mono<MockSessionResponse> createMockSession(@RequestBody String specText) {
        return this.webClient.post()
                .uri("/mock/start")
                .contentType(MediaType.APPLICATION_JSON)
                .bodyValue(new MockStartRequest(specText))
                .retrieve()
                .bodyToMono(MockSessionDetails.class)
                .map(mockSessionDetails -> {
                    String fullMockUrl = "http://localhost:8000" + mockSessionDetails.baseUrl();
                    return new MockSessionResponse(mockSessionDetails.mockId(), fullMockUrl);
                });
    }

    @PutMapping("/{sessionId}/spec")
    public Mono<ResponseEntity<String>> updateSessionSpec(@PathVariable String sessionId, @RequestBody String specText) {
        return this.webClient.put()
                .uri("/mock/" + sessionId)
                .contentType(MediaType.APPLICATION_JSON)
                .bodyValue(specText)
                .retrieve()
                .toEntity(String.class);
    }

    @GetMapping("/{sessionId}/spec")
    public ResponseEntity<String> getSessionSpec(@PathVariable String sessionId) {
        OpenAPI openAPI = sessionService.getSpecForSession(sessionId);
        if (Objects.isNull(openAPI)) {
            return ResponseEntity.notFound().build();
        }
        String specText = Yaml.pretty(openAPI);
        return ResponseEntity.ok(specText);

    }
}
