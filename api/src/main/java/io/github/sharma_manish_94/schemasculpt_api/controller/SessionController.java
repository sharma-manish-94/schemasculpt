package io.github.sharma_manish_94.schemasculpt_api.controller;

import io.github.sharma_manish_94.schemasculpt_api.dto.CreateMockSessionRequest;
import io.github.sharma_manish_94.schemasculpt_api.dto.MockSessionDetails;
import io.github.sharma_manish_94.schemasculpt_api.dto.MockSessionResponse;
import io.github.sharma_manish_94.schemasculpt_api.dto.MockStartRequest;
import io.github.sharma_manish_94.schemasculpt_api.dto.SessionResponse;
import io.github.sharma_manish_94.schemasculpt_api.dto.request.CreateSessionRequest;
import io.github.sharma_manish_94.schemasculpt_api.dto.request.UpdateSpecRequest;
import io.github.sharma_manish_94.schemasculpt_api.exception.SessionNotFoundException;
import io.github.sharma_manish_94.schemasculpt_api.service.SessionService;
import io.github.sharma_manish_94.schemasculpt_api.util.OpenAPIEnumFixer;
import io.swagger.v3.core.util.Yaml;
import io.swagger.v3.oas.models.OpenAPI;
import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import java.util.Objects;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

@RestController
@RequestMapping("/api/v1/sessions")
@Validated
@Slf4j
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
  public ResponseEntity<SessionResponse> createSession(
      @Valid @RequestBody CreateSessionRequest request) {
    log.info("Creating new session");
    String sessionId = sessionService.createSession(request.specText());
    log.info("Created session with ID: {}", sessionId);
    return ResponseEntity.status(HttpStatus.CREATED).body(new SessionResponse(sessionId));
  }

  @PostMapping("/mock")
  public Mono<MockSessionResponse> createMockSession(
      @RequestBody CreateMockSessionRequest request) {
    return this.webClient
        .post()
        .uri("/mock/start")
        .contentType(MediaType.APPLICATION_JSON)
        .bodyValue(new MockStartRequest(request.specText()))
        .retrieve()
        .bodyToMono(MockSessionDetails.class)
        .map(
            mockSessionDetails -> {
              String fullMockUrl = "http://localhost:8000" + mockSessionDetails.baseUrl();
              return new MockSessionResponse(mockSessionDetails.mockId(), fullMockUrl);
            });
  }

  @GetMapping("/{sessionId}/spec")
  public ResponseEntity<String> getSessionSpec(
      @PathVariable @NotBlank(message = "Session ID cannot be blank") String sessionId) {
    log.debug("Retrieving spec for session: {}", sessionId);

    OpenAPI openAPI = sessionService.getSpecForSession(sessionId);
    if (Objects.isNull(openAPI)) {
      throw new SessionNotFoundException(sessionId);
    }

    String specText = Yaml.pretty(openAPI);

    specText = OpenAPIEnumFixer.fixEnums(specText);

    return ResponseEntity.ok(specText);
  }

  @PutMapping("/{sessionId}/spec")
  public ResponseEntity<Void> updateSessionSpec(
      @PathVariable @NotBlank(message = "Session ID cannot be blank") String sessionId,
      @Valid @RequestBody UpdateSpecRequest request) {
    log.debug("Updating spec for session: {}", sessionId);

    sessionService.updateSessionSpec(sessionId, request.specText());
    return ResponseEntity.noContent().build();
  }

  @DeleteMapping("/{sessionId}")
  public ResponseEntity<Void> deleteSession(
      @PathVariable @NotBlank(message = "Session ID cannot be blank") String sessionId) {
    log.info("Deleting session: {}", sessionId);

    sessionService.closeSession(sessionId);
    return ResponseEntity.noContent().build();
  }
}