package io.github.sharmanish.schemasculpt.service.impl;

import io.github.sharmanish.schemasculpt.dto.analysis.CodeMetrics;
import io.github.sharmanish.schemasculpt.dto.analysis.CodeOwnership;
import io.github.sharmanish.schemasculpt.dto.analysis.TestCoverage;
import io.github.sharmanish.schemasculpt.dto.response.ImplementationCodeResponse;
import io.github.sharmanish.schemasculpt.service.RepoMindService;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

@Service
@Slf4j
public class RepoMindServiceImpl implements RepoMindService {

  private final WebClient.Builder webClientBuilder;

  @Value("${repomind.server.url}")
  private String repoMindServerUrl;

  public RepoMindServiceImpl(WebClient.Builder webClientBuilder) {
    this.webClientBuilder = webClientBuilder;
  }

  // --- DTOs for internal communication ---
  private record McpToolCallRequest(String tool_name, Map<String, Object> arguments) {}

  private record RepoMindCodeChunk(
      String file_path, String content, int start_line, String language) {}

  // --- Helper method for calling RepoMind tools ---
  private <T> Mono<T> callRepoMindTool(
      String toolName, Map<String, Object> args, Class<T> responseClass) {
    log.debug("Calling RepoMind tool: {} with args: {}", toolName, args);
    WebClient client = webClientBuilder.baseUrl(repoMindServerUrl).build();
    McpToolCallRequest requestPayload = new McpToolCallRequest(toolName, args);

    return client
        .post()
        .uri("/call_tool")
        .body(Mono.just(requestPayload), McpToolCallRequest.class)
        .retrieve()
        .bodyToMono(responseClass)
        .doOnError(
            error ->
                log.error("Error calling RepoMind tool '{}': {}", toolName, error.getMessage()));
  }

  // --- Service method implementations ---

  /**
   * Triggers repository indexing in RepoMind. Returns a Mono for proper error handling - callers
   * can subscribe and handle errors appropriately.
   *
   * @param repoPath Path to the repository on disk
   * @param repoName Name of the repository for identification
   * @return Mono<Void> that completes when indexing is triggered (not when indexing completes)
   */
  @Override
  public Mono<Void> triggerRepoIndex(String repoPath, String repoName) {
    log.info("Triggering RepoMind indexing for repo: '{}', path: '{}'", repoName, repoPath);
    Map<String, Object> args = Map.of("repo_path", repoPath, "repo_name", repoName);

    return callRepoMindTool("index_repo", args, Void.class)
        .doOnSuccess(
            aVoid -> log.info("Successfully triggered RepoMind indexing for '{}'", repoName))
        .doOnError(
            error ->
                log.error(
                    "Failed to trigger RepoMind indexing for '{}': {}",
                    repoName,
                    error.getMessage()))
        .then();
  }

  @Override
  public Mono<ImplementationCodeResponse> getImplementationCode(
      String repoName, String operationId) {
    log.debug(
        "Fetching implementation from RepoMind for repo: '{}', symbol: '{}'",
        repoName,
        operationId);
    Map<String, Object> args = Map.of("symbol_name", operationId, "repo_filter", repoName);

    return callRepoMindTool("get_context", args, RepoMindCodeChunk[].class)
        .flatMap(
            chunks -> {
              if (chunks == null || chunks.length == 0) {
                log.warn(
                    "No implementation found in RepoMind for symbol '{}' in repo '{}'",
                    operationId,
                    repoName);
                return Mono.error(
                    new RuntimeException("No implementation found for symbol: " + operationId));
              }
              RepoMindCodeChunk chunk = chunks[0];
              log.debug("Found implementation at {}", chunk.file_path());
              return Mono.just(
                  new ImplementationCodeResponse(
                      chunk.file_path(), chunk.content(), chunk.start_line(), chunk.language()));
            });
  }

  @Override
  public Mono<CodeMetrics> getMetrics(String repoName, String symbolName) {
    Map<String, Object> args = Map.of("repo_filter", repoName, "symbol_name", symbolName);
    return callRepoMindTool("get_metrics", args, CodeMetrics.class)
        .doOnError(
            error ->
                log.warn(
                    "Failed to get metrics for symbol '{}' in repo '{}': {}. Using default.",
                    symbolName,
                    repoName,
                    error.getMessage()))
        .onErrorReturn(new CodeMetrics(0.0));
  }

  @Override
  public Mono<TestCoverage> findTests(String repoName, String symbolName) {
    Map<String, Object> args = Map.of("repo_filter", repoName, "symbol_name", symbolName);
    return callRepoMindTool("find_tests", args, TestCoverage.class)
        .doOnError(
            error ->
                log.warn(
                    "Failed to find tests for symbol '{}' in repo '{}': {}. Using default.",
                    symbolName,
                    repoName,
                    error.getMessage()))
        .onErrorReturn(new TestCoverage(0, 0));
  }

  @Override
  public Mono<CodeOwnership> analyzeOwnership(String repoName, String filePath) {
    Map<String, Object> args = Map.of("repo_filter", repoName, "file_paths", List.of(filePath));
    return callRepoMindTool("analyze_ownership", args, CodeOwnership.class)
        .doOnError(
            error ->
                log.warn(
                    "Failed to analyze ownership for '{}' in repo '{}': {}. Using default.",
                    filePath,
                    repoName,
                    error.getMessage()))
        .onErrorReturn(new CodeOwnership(Collections.emptyList()));
  }
}
