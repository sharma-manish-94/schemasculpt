package io.github.sharmanish.schemasculpt.controller;

import io.github.sharmanish.schemasculpt.dto.CreateMockSessionRequest;
import io.github.sharmanish.schemasculpt.dto.MockSessionDetails;
import io.github.sharmanish.schemasculpt.dto.MockSessionResponse;
import io.github.sharmanish.schemasculpt.dto.MockStartRequest;
import io.github.sharmanish.schemasculpt.dto.SessionResponse;
import io.github.sharmanish.schemasculpt.dto.request.CreateSessionRequest;
import io.github.sharmanish.schemasculpt.dto.request.LinkRepositoryRequest;
import io.github.sharmanish.schemasculpt.exception.ValidationException;
import io.github.sharmanish.schemasculpt.service.RepoMindService;
import io.github.sharmanish.schemasculpt.util.LogSanitizer;
import java.util.Map;
import io.github.sharmanish.schemasculpt.dto.request.UpdateSpecRequest;
import io.github.sharmanish.schemasculpt.exception.SessionNotFoundException;
import io.github.sharmanish.schemasculpt.service.SessionService;
import io.github.sharmanish.schemasculpt.util.OpenApiEnumFixer;
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
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

@RestController
@RequestMapping("/api/v1/sessions")
@Validated
@Slf4j
public class SessionController {
  private final SessionService sessionService;
  private final WebClient webClient;
  private final RepoMindService repoMindService;

  public SessionController(
      final SessionService sessionService,
      final WebClient.Builder webClientBuilder,
      final RepoMindService repoMindService,
      @Value("${ai.service.url}") String aiServiceUrl) {
    this.sessionService = sessionService;
    this.webClient = webClientBuilder.baseUrl(aiServiceUrl).build();
    this.repoMindService = repoMindService;
  }

  @PostMapping
  public ResponseEntity<SessionResponse> createSession(
      @Valid @RequestBody CreateSessionRequest request) {
    log.info("Creating new session");
    String sessionId = sessionService.createSession(request.specText());
    log.info("Created session with ID: {}", LogSanitizer.sanitize(sessionId));
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
    log.debug("Retrieving spec for session: {}", LogSanitizer.sanitize(sessionId));

    OpenAPI openAPI = sessionService.getSpecForSession(sessionId);
    if (Objects.isNull(openAPI)) {
      throw new SessionNotFoundException(sessionId);
    }

    String specText = Yaml.pretty(openAPI);

    specText = OpenApiEnumFixer.fixEnums(specText);

    return ResponseEntity.ok(specText);
  }

  @PutMapping("/{sessionId}/spec")
  public ResponseEntity<Void> updateSessionSpec(
      @PathVariable @NotBlank(message = "Session ID cannot be blank") String sessionId,
      @Valid @RequestBody UpdateSpecRequest request) {
    log.debug("Updating spec for session: {}", LogSanitizer.sanitize(sessionId));

    sessionService.updateSessionSpec(sessionId, request.specText());
    return ResponseEntity.noContent().build();
  }

  @DeleteMapping("/{sessionId}")
  public ResponseEntity<Void> deleteSession(
      @PathVariable @NotBlank(message = "Session ID cannot be blank") String sessionId) {
    log.info("Deleting session: {}", LogSanitizer.sanitize(sessionId));

    sessionService.closeSession(sessionId);
    return ResponseEntity.noContent().build();
  }
  @PostMapping("/{sessionId}/local-repository")
  public ResponseEntity<Map<String, String>> linkLocalRepository(
      @PathVariable @NotBlank(message = "Session ID cannot be blank") String sessionId,
      @Valid @RequestBody LinkRepositoryRequest request) {

    if (!request.isSafePath()) {
      log.warn(
          "Rejected unsafe repository path '{}' for session {}",
          LogSanitizer.sanitize(request.path()),
          LogSanitizer.sanitize(sessionId));
      throw new ValidationException(
          "Invalid repository path. Must be an absolute path without path traversal sequences.");
    }

    log.info(
        "Linking local repository '{}' for session {}",
        LogSanitizer.sanitize(request.path()),
        LogSanitizer.sanitize(sessionId));

    // Derive a repo name from the last path segment
    String[] segments = request.path().replace("\\", "/").split("/");
    String repoName = segments[segments.length - 1];
    if (repoName.isBlank()) {
      repoName = "local-repo";
    }

    final String finalRepoName = repoName;
    repoMindService
        .triggerRepoIndex(request.path(), finalRepoName)
        .subscribe(
            unused -> log.info("RepoMind indexing triggered for '{}'", finalRepoName),
            error ->
                log.error(
                    "Failed to trigger indexing for '{}': {}", finalRepoName, error.getMessage()));

    return ResponseEntity.ok(
        Map.of("path", request.path(), "repoName", finalRepoName, "status", "indexing"));
  }
  @GetMapping("/repomind-health")
  public Mono<ResponseEntity<Object>> repomindHealth() {
    return webClient
        .get()
        .uri("/ai/repomind/health")
        .retrieve()
        .bodyToMono(Object.class)
        .map(ResponseEntity::ok)
        .onErrorResume(
            error -> {
              log.warn("RepoMind health check failed: {}", error.getMessage());
              return Mono.just(
                  ResponseEntity.status(503)
                      .body(
                          (Object)
                              java.util.Map.of(
                                  "status", "unavailable",
                                  "error", error.getMessage(),
                                  "hint",
                                      "Ensure the AI service is running and RepoMind is"
                                          + " installed (pip install repomind).")));
            });
  }
}
