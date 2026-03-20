package io.github.sharmanish.schemasculpt.service;

import io.github.sharmanish.schemasculpt.dto.analysis.AuthVerificationResponse;
import io.github.sharmanish.schemasculpt.dto.analysis.CodeMetrics;
import io.github.sharmanish.schemasculpt.dto.analysis.CodeOwnership;
import io.github.sharmanish.schemasculpt.dto.analysis.ContractVerificationResponse;
import io.github.sharmanish.schemasculpt.dto.analysis.IndexingResult;
import io.github.sharmanish.schemasculpt.dto.analysis.IndexingStats;
import io.github.sharmanish.schemasculpt.dto.analysis.SpecCorrelationResponse;
import io.github.sharmanish.schemasculpt.dto.analysis.TestCoverage;
import io.github.sharmanish.schemasculpt.dto.response.ImplementationCodeResponse;
import reactor.core.publisher.Mono;

public interface RepoMindService {
  /**
   * Triggers the indexing of a repository in the RepoMind service.
   *
   * @param repoPath The absolute local path to the repository to be indexed.
   * @param repoName A unique name to identify the repository within RepoMind.
   * @return A Mono containing the indexing result.
   */
  Mono<IndexingResult> triggerRepoIndex(String repoPath, String repoName);

  /**
   * Fetches current indexing statistics from RepoMind.
   *
   * @return A Mono containing the indexing statistics.
   */
  Mono<IndexingStats> getIndexStats();

  /**
   * Asynchronously fetches the implementation code for a given operation ID from RepoMind.
   *
   * @param repoName The name of the repository to search within.
   * @param operationId The operationId from the OpenAPI spec, used as the symbol name.
   * @return A Mono containing the implementation code details.
   */
  Mono<ImplementationCodeResponse> getImplementationCode(String repoName, String operationId);

  /**
   * Correlates an OpenAPI endpoint to its implementation handler in the source code.
   *
   * @param repoName The repository name.
   * @param path The OpenAPI path.
   * @param method The HTTP method.
   * @return A Mono containing the correlation result.
   */
  Mono<SpecCorrelationResponse> correlateSpecToCode(String repoName, String path, String method);

  /**
   * Verifies the API contract (parameters, schemas) against the source code.
   *
   * @param repoName The repository name.
   * @param path The OpenAPI path.
   * @param method The HTTP method.
   * @return A Mono containing the contract verification result.
   */
  Mono<ContractVerificationResponse> verifyContract(String repoName, String path, String method);

  /**
   * Verifies the authentication contract against the source code.
   *
   * @param repoName The repository name.
   * @param path The OpenAPI path.
   * @param method The HTTP method.
   * @param declaredSecurity The security requirements from the spec.
   * @return A Mono containing the auth verification result.
   */
  Mono<AuthVerificationResponse> verifyAuthContract(
      String repoName, String path, String method, Object declaredSecurity);

  /**
   * Intelligently correlates an OpenAPI endpoint to its implementation handler using LLM reasoning
   * and RepoMind tools.
   *
   * @param repoName The repository name.
   * @param path The OpenAPI path.
   * @param method The HTTP method.
   * @param operationId The optional operation ID.
   * @return A Mono containing the correlation result.
   */
  Mono<SpecCorrelationResponse> intelligentCorrelate(
      String repoName, String path, String method, String operationId);

  /**
   * Asynchronously fetches code metrics for a given symbol from RepoMind.
   *
   * @param repoName The name of the repository to search within.
   * @param symbolName The name of the symbol (e.g., function or method).
   * @return A Mono containing the code metrics.
   */
  Mono<CodeMetrics> getMetrics(String repoName, String symbolName);

  /**
   * Asynchronously finds tests related to a given symbol from RepoMind.
   *
   * @param repoName The name of the repository to search within.
   * @param symbolName The name of the symbol.
   * @return A Mono containing the test coverage information.
   */
  Mono<TestCoverage> findTests(String repoName, String symbolName);

  /**
   * Asynchronously analyzes the ownership of a given file from RepoMind.
   *
   * @param repoName The name of the repository to search within.
   * @param filePath The path to the file.
   * @return A Mono containing the code ownership information.
   */
  Mono<CodeOwnership> analyzeOwnership(String repoName, String filePath);
}
