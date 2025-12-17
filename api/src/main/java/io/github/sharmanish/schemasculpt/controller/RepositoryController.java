package io.github.sharmanish.schemasculpt.controller;

import io.github.sharmanish.schemasculpt.dto.repository.BrowseTreeRequest;
import io.github.sharmanish.schemasculpt.dto.repository.BrowseTreeResponse;
import io.github.sharmanish.schemasculpt.dto.repository.ReadFileRequest;
import io.github.sharmanish.schemasculpt.dto.repository.ReadFileResponse;
import io.github.sharmanish.schemasculpt.dto.repository.RepositoryConnectionRequest;
import io.github.sharmanish.schemasculpt.dto.repository.RepositoryConnectionResponse;
import io.github.sharmanish.schemasculpt.service.RepositoryService;
import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import reactor.core.publisher.Mono;

/**
 * REST controller for repository operations.
 * <p>
 * Provides endpoints for connecting to and browsing repositories via MCP.
 */
@RestController
@RequestMapping("/api/v1/repository")
@Validated
@Slf4j
public class RepositoryController {

  private final RepositoryService repositoryService;

  public RepositoryController(RepositoryService repositoryService) {
    this.repositoryService = repositoryService;
  }

  /**
   * Connect to a repository provider (GitHub, GitLab, etc.)
   *
   * @param sessionId Session ID from header
   * @param request   Connection request with provider and access token
   * @return Connection response
   */
  @PostMapping("/connect")
  public Mono<ResponseEntity<RepositoryConnectionResponse>> connectRepository(
      @RequestHeader("X-Session-ID") @NotBlank String sessionId,
      @Valid @RequestBody RepositoryConnectionRequest request) {

    log.info("Connection request for session: {} to provider: {}", sessionId,
        request.getProvider());

    return repositoryService.connect(sessionId, request)
        .map(response -> {
          // Store context in session after successful connection
          if (response.isSuccess()) {
            repositoryService.storeRepositoryContext(
                sessionId,
                request.getProvider(),
                request.getAccessToken()
            );
          }
          return ResponseEntity.ok(response);
        })
        .onErrorResume(error -> {
          log.error("Error connecting to repository provider: {}", error.getMessage());
          return Mono.just(ResponseEntity.status(HttpStatus.BAD_REQUEST)
              .body(new RepositoryConnectionResponse(
                  false,
                  "Failed to connect: " + error.getMessage(),
                  request.getProvider()
              )));
        });
  }

  /**
   * Disconnect from repository provider
   *
   * @param sessionId Session ID from header
   * @return Success response
   */
  @PostMapping("/disconnect")
  public Mono<ResponseEntity<String>> disconnectRepository(
      @RequestHeader("X-Session-ID") @NotBlank String sessionId) {

    log.info("Disconnect request for session: {}", sessionId);

    return repositoryService.disconnect(sessionId)
        .then(Mono.just(
            ResponseEntity.ok("{\"success\": true, \"message\": \"Disconnected successfully\"}")))
        .onErrorResume(error -> {
          log.error("Error disconnecting from repository: {}", error.getMessage());
          return Mono.just(ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
              .body("{\"success\": false, \"message\": \"" + error.getMessage() + "\"}"));
        });
  }

  /**
   * Browse repository tree
   *
   * @param sessionId Session ID from header
   * @param request   Browse request
   * @return Tree contents
   */
  @PostMapping("/browse")
  public Mono<ResponseEntity<BrowseTreeResponse>> browseTree(
      @RequestHeader("X-Session-ID") @NotBlank String sessionId,
      @Valid @RequestBody BrowseTreeRequest request) {

    log.info("Browse tree request for session: {} - {}/{}/{}",
        sessionId, request.getOwner(), request.getRepo(), request.getPath());

    return repositoryService.browseTree(sessionId, request)
        .map(ResponseEntity::ok)
        .onErrorResume(error -> {
          log.error("Error browsing tree: {}", error.getMessage());
          return Mono.just(ResponseEntity.status(HttpStatus.BAD_REQUEST).build());
        });
  }

  /**
   * Read file from repository
   *
   * @param sessionId Session ID from header
   * @param request   Read file request
   * @return File content
   */
  @PostMapping("/file")
  public Mono<ResponseEntity<ReadFileResponse>> readFile(
      @RequestHeader("X-Session-ID") @NotBlank String sessionId,
      @Valid @RequestBody ReadFileRequest request) {

    log.info("Read file request for session: {} - {}/{}/{}",
        sessionId, request.getOwner(), request.getRepo(), request.getPath());

    return repositoryService.readFile(sessionId, request)
        .map(ResponseEntity::ok)
        .onErrorResume(error -> {
          log.error("Error reading file: {}", error.getMessage());
          return Mono.just(ResponseEntity.status(HttpStatus.NOT_FOUND).build());
        });
  }

  /**
   * Get repository connection status for session
   *
   * @param sessionId Session ID from header
   * @return Connection status
   */
  @GetMapping("/status")
  public ResponseEntity<RepositoryConnectionResponse> getConnectionStatus(
      @RequestHeader("X-Session-ID") @NotBlank String sessionId) {

    log.debug("Checking repository connection status for session: {}", sessionId);

    RepositoryConnectionResponse context = repositoryService.getRepositoryContext(sessionId);

    if (context != null) {
      return ResponseEntity.ok(context);
    } else {
      return ResponseEntity.ok(new RepositoryConnectionResponse(
          false,
          "Not connected to any repository provider",
          null
      ));
    }
  }
}
