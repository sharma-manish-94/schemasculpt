package io.github.sharmanish.schemasculpt.service;

import io.github.sharmanish.schemasculpt.dto.analysis.CodeMetrics;
import io.github.sharmanish.schemasculpt.dto.analysis.CodeOwnership;
import io.github.sharmanish.schemasculpt.dto.analysis.TestCoverage;
import io.github.sharmanish.schemasculpt.dto.response.ImplementationCodeResponse;
import reactor.core.publisher.Mono;

public interface RepoMindService {
  /**
   * Asynchronously triggers the indexing of a repository in the RepoMind service.
   *
   * @param repoPath The absolute local path to the repository to be indexed.
   * @param repoName A unique name to identify the repository within RepoMind.
   */
  void triggerRepoIndex(String repoPath, String repoName);

  /**
   * Asynchronously fetches the implementation code for a given operation ID from RepoMind.
   *
   * @param repoName The name of the repository to search within.
   * @param operationId The operationId from the OpenAPI spec, used as the symbol name.
   * @return A Mono containing the implementation code details.
   */
  Mono<ImplementationCodeResponse> getImplementationCode(String repoName, String operationId);

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
