package io.github.sharmanish.schemasculpt.service;

import io.github.sharmanish.schemasculpt.dto.repository.BrowseTreeRequest;
import io.github.sharmanish.schemasculpt.dto.repository.BrowseTreeResponse;
import io.github.sharmanish.schemasculpt.dto.repository.ReadFileRequest;
import io.github.sharmanish.schemasculpt.dto.repository.ReadFileResponse;
import io.github.sharmanish.schemasculpt.dto.repository.RepositoryConnectionRequest;
import io.github.sharmanish.schemasculpt.dto.repository.RepositoryConnectionResponse;
import java.util.Objects;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

/**
 * Service for repository operations.
 *
 * <p>This service proxies repository requests to the AI Service which handles MCP integration with
 * repository providers (GitHub, GitLab, etc.)
 */
@Service
@Slf4j
public class RepositoryService {

  private final WebClient webClient;

  public RepositoryService(
      WebClient.Builder webClientBuilder, @Value("${ai.service.url}") String aiServiceUrl) {
    Objects.requireNonNull(webClientBuilder, "webClientBuilder must not be null");
    Objects.requireNonNull(aiServiceUrl, "aiServiceUrl must not be null");
    this.webClient = webClientBuilder.baseUrl(aiServiceUrl).build();
  }

  /**
   * Connect to a repository provider.
   *
   * @param sessionId Session ID
   * @param request Connection request with provider and access token
   * @return Connection response
   */
  public Mono<RepositoryConnectionResponse> connect(
      String sessionId, RepositoryConnectionRequest request) {
    log.info(
        "Connecting to repository provider: {} for session: {}", request.provider(), sessionId);
    log.debug(
        "Request payload - provider: {}, accessToken: {}",
        request.provider(),
        request.accessToken() != null ? "***" : "null");

    return webClient
        .post()
        .uri("/api/repository/connect")
        .header(HttpHeaders.CONTENT_TYPE, MediaType.APPLICATION_JSON_VALUE)
        .header("X-Session-ID", sessionId)
        .bodyValue(request)
        .retrieve()
        .onStatus(
            status -> status.value() == 422,
            response -> {
              return response
                  .bodyToMono(String.class)
                  .flatMap(
                      body -> {
                        log.error("422 Validation error from AI service: {}", body);
                        return Mono.error(new RuntimeException("Validation failed: " + body));
                      });
            })
        .bodyToMono(RepositoryConnectionResponse.class)
        .doOnSuccess(
            response ->
                log.info(
                    "Successfully connected to {} for session: {}",
                    request.provider(),
                    sessionId))
        .doOnError(
            error ->
                log.error(
                    "Failed to connect to repository provider for session: {}", sessionId, error));
  }

  /**
   * Disconnect from repository provider.
   *
   * @param sessionId Session ID
   * @return Success response
   */
  public Mono<Void> disconnect(String sessionId) {
    log.info("Disconnecting session: {} from repository provider", sessionId);

    return webClient
        .post()
        .uri("/api/repository/disconnect")
        .header("X-Session-ID", sessionId)
        .retrieve()
        .bodyToMono(Void.class)
        .doOnSuccess(v -> log.info("Successfully disconnected session: {}", sessionId))
        .doOnError(error -> log.error("Error disconnecting session: {}", sessionId, error));
  }

  /**
   * Browse repository tree.
   *
   * @param sessionId Session ID
   * @param request Browse request
   * @return Tree contents
   */
  public Mono<BrowseTreeResponse> browseTree(String sessionId, BrowseTreeRequest request) {
    log.debug(
        "Browsing tree: {}/{}/{} for session: {}",
        request.owner(),
        request.repo(),
        request.path(),
        sessionId);
    log.debug(
        "Browse request payload - owner: {}, repo: {}, path: {}, branch: {}",
        request.owner(),
        request.repo(),
        request.path(),
        request.branch());

    return webClient
        .post()
        .uri("/api/repository/browse")
        .header(HttpHeaders.CONTENT_TYPE, MediaType.APPLICATION_JSON_VALUE)
        .header("X-Session-ID", sessionId)
        .bodyValue(request)
        .retrieve()
        .onStatus(
            status -> status.value() == 422,
            response -> {
              return response
                  .bodyToMono(String.class)
                  .flatMap(
                      body -> {
                        log.error("422 Validation error from AI service: {}", body);
                        return Mono.error(new RuntimeException("Validation failed: " + body));
                      });
            })
        .bodyToMono(BrowseTreeResponse.class)
        .doOnSuccess(
            response ->
                log.debug(
                    "Retrieved {} files from {}/{}/{}",
                    response.files().size(),
                    request.owner(),
                    request.repo(),
                    request.path()))
        .doOnError(error -> log.error("Error browsing tree for session: {}", sessionId, error));
  }

  /**
   * Read file from repository.
   *
   * @param sessionId Session ID
   * @param request Read file request
   * @return File content
   */
  public Mono<ReadFileResponse> readFile(String sessionId, ReadFileRequest request) {
    log.info(
        "Reading file: {}/{}/{} for session: {}",
        request.owner(),
        request.repo(),
        request.path(),
        sessionId);

    return webClient
        .post()
        .uri("/api/repository/file")
        .header(HttpHeaders.CONTENT_TYPE, MediaType.APPLICATION_JSON_VALUE)
        .header("X-Session-ID", sessionId)
        .bodyValue(request)
        .retrieve()
        .bodyToMono(ReadFileResponse.class)
        .doOnSuccess(
            response ->
                log.info(
                    "Successfully read file: {} ({} bytes)", request.path(), response.size()))
        .doOnError(error -> log.error("Error reading file for session: {}", sessionId, error));
  }

  /**
   * Store repository connection info in session (Redis). This will be called after successful
   * connection.
   *
   * @param sessionId Session ID
   * @param provider Provider name
   * @param accessToken Access token (encrypted)
   */
  public void storeRepositoryContext(String sessionId, String provider, String accessToken) {
    // TODO: Implement Redis storage for repository context
    // This will store:
    // - Provider name
    // - Encrypted access token
    // - Connection timestamp
    // - Last accessed repository
    log.info("Storing repository context for session: {} (provider: {})", sessionId, provider);
  }

  /**
   * Get repository context from session.
   *
   * @param sessionId Session ID
   * @return Repository context or null if not connected
   */
  public RepositoryConnectionResponse getRepositoryContext(String sessionId) {
    // TODO: Implement Redis retrieval
    log.debug("Retrieving repository context for session: {}", sessionId);
    return null;
  }
}
