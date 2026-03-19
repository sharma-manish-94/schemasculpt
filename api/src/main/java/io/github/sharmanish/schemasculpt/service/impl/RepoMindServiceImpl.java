package io.github.sharmanish.schemasculpt.service.impl;

import io.github.sharmanish.schemasculpt.dto.analysis.AuthVerificationResponse;
import io.github.sharmanish.schemasculpt.dto.analysis.CodeMetrics;
import io.github.sharmanish.schemasculpt.dto.analysis.CodeOwnership;
import io.github.sharmanish.schemasculpt.dto.analysis.ContractVerificationResponse;
import io.github.sharmanish.schemasculpt.dto.analysis.IndexingResult;
import io.github.sharmanish.schemasculpt.dto.analysis.IndexingStats;
import io.github.sharmanish.schemasculpt.dto.analysis.SpecCorrelationResponse;
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
import tools.jackson.databind.JsonNode;
import tools.jackson.databind.json.JsonMapper;

@Service
@Slf4j
public class RepoMindServiceImpl implements RepoMindService {

  private final WebClient.Builder webClientBuilder;
  private final JsonMapper objectMapper;

  @Value("${repomind.server.url}")
  private String repoMindServerUrl;

  public RepoMindServiceImpl(WebClient.Builder webClientBuilder, JsonMapper objectMapper) {
    this.webClientBuilder = webClientBuilder;
    this.objectMapper = objectMapper;
  }

  // --- DTOs for internal communication ---
  private record McpToolCallRequest(String tool_name, Map<String, Object> arguments) {}

  private record RepoMindCodeChunk(String file, String code, int start_line, String language) {}

  private record RepoMindContextResponse(
      String symbol, boolean found, int match_count, List<RepoMindCodeChunk> results) {}

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
        .bodyToMono(JsonNode.class)
        .flatMap(
            node -> {
              JsonNode resultNode = node.get("result");
              if (resultNode == null || resultNode.isNull()) {
                return Mono.empty();
              }
              try {
                T value = objectMapper.convertValue(resultNode, responseClass);
                return value != null ? Mono.just(value) : Mono.empty();
              } catch (IllegalArgumentException e) {
                log.error("Failed to convert RepoMind result for tool '{}': {}", toolName, e.getMessage());
                return Mono.error(e);
              }
            })
        .doOnError(
            error ->
                log.error("Error calling RepoMind tool '{}': {}", toolName, error.getMessage()));
  }

  // --- Service method implementations ---

  @Override
  public Mono<IndexingResult> triggerRepoIndex(String repoPath, String repoName) {
    log.info("Triggering RepoMind indexing for repo: '{}', path: '{}'", repoName, repoPath);

    return getIndexStats()
        .flatMap(
            stats -> {
              boolean alreadyIndexed = stats.repositories() != null && stats.repositories().contains(repoName);

              Map<String, Object> args = Map.of(
                  "repo_path", repoPath,
                  "repo_name", repoName,
                  "incremental", alreadyIndexed
              );

              return callRepoMindTool("index_repo", args, IndexingResult.class)
                  .doOnSuccess(result -> log.info("Successfully triggered indexing for '{}'. Status: {}", repoName, result != null ? result.status() : "unknown"))
                  .doOnError(error -> log.error("Failed to trigger indexing for '{}': {}", repoName, error.getMessage()));
            });
  }

  @Override
  public Mono<IndexingStats> getIndexStats() {
    return callRepoMindTool("get_index_stats", Collections.emptyMap(), IndexingStats.class)
        .onErrorReturn(new IndexingStats(0, Collections.emptyList(), Collections.emptyMap(), Collections.emptyMap()));
  }

  @Override
  public Mono<ImplementationCodeResponse> getImplementationCode(
      String repoName, String operationId) {
    log.debug(
        "Fetching implementation from RepoMind for repo: '{}', symbol: '{}'",
        repoName,
        operationId);
    Map<String, Object> args = Map.of("symbol_name", operationId, "repo_filter", repoName);

    return callRepoMindTool("get_context", args, RepoMindContextResponse.class)
        .flatMap(
            response -> {
              if (response == null || !response.found() || response.results().isEmpty()) {
                log.warn(
                    "No implementation found in RepoMind for symbol '{}' in repo '{}'",
                    operationId,
                    repoName);
                return Mono.error(
                    new RuntimeException("No implementation found for symbol: " + operationId));
              }
              RepoMindCodeChunk chunk = response.results().get(0);
              log.debug("Found implementation at {}", chunk.file());
              return Mono.just(
                  new ImplementationCodeResponse(
                      chunk.file(), chunk.code(), chunk.start_line(), chunk.language()));
            });
  }

  @Override
  public Mono<SpecCorrelationResponse> correlateSpecToCode(
      String repoName, String path, String method) {
    Map<String, Object> args =
        Map.of("repo_name", repoName, "openapi_path", path, "http_method", method);
    return callRepoMindTool("correlate_spec_to_code", args, SpecCorrelationResponse.class);
  }

  @Override
  public Mono<SpecCorrelationResponse> intelligentCorrelate(
      String repoName, String path, String method, String operationId) {
    Map<String, Object> args = Map.of(
        "repo_name", repoName,
        "path", path,
        "method", method
    );
    // Add operationId if present
    if (operationId != null && !operationId.isBlank()) {
        Map<String, Object> mutableArgs = new java.util.HashMap<>(args);
        mutableArgs.put("operation_id", operationId);
        args = mutableArgs;
    }

    log.debug("Triggering intelligent correlation for {} {} in {}", method, path, repoName);

    WebClient client = webClientBuilder.baseUrl(repoMindServerUrl).build();
    return client
        .post()
        .uri("/intelligent_correlate")
        .bodyValue(args)
        .retrieve()
        .bodyToMono(SpecCorrelationResponse.class)
        .doOnError(error -> log.error("Intelligent correlation failed: {}", error.getMessage()));
  }

  @Override
  public Mono<ContractVerificationResponse> verifyContract(
      String repoName, String path, String method) {
    Map<String, Object> args =
        Map.of("repo_name", repoName, "openapi_path", path, "http_method", method);
    return callRepoMindTool("verify_api_contract", args, ContractVerificationResponse.class);
  }

  @Override
  public Mono<AuthVerificationResponse> verifyAuthContract(
      String repoName, String path, String method, Object declaredSecurity) {
    Map<String, Object> args =
        Map.of(
            "repo_name",
            repoName,
            "openapi_path",
            path,
            "http_method",
            method,
            "declared_security",
            declaredSecurity);
    return callRepoMindTool("verify_auth_contract_deep", args, AuthVerificationResponse.class);
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
