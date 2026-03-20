package io.github.sharmanish.schemasculpt.controller;

import io.github.sharmanish.schemasculpt.dto.analysis.AuthVerificationResponse;
import io.github.sharmanish.schemasculpt.dto.analysis.ContractVerificationResponse;
import io.github.sharmanish.schemasculpt.dto.response.ImplementationCodeResponse;
import io.github.sharmanish.schemasculpt.dto.response.ImplementationIntelligenceResponse;
import io.github.sharmanish.schemasculpt.entity.Project;
import io.github.sharmanish.schemasculpt.exception.ValidationException;
import io.github.sharmanish.schemasculpt.security.CustomOAuth2User;
import io.github.sharmanish.schemasculpt.service.ProjectService;
import io.github.sharmanish.schemasculpt.service.RepoMindService;
import java.util.Collections;
import java.util.List;
import java.util.regex.Pattern;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import reactor.core.publisher.Mono;

/**
 * REST controller for querying code intelligence about API operation implementations.
 *
 * <p>Correlates OpenAPI spec operations to their source-code handlers via RepoMind and returns
 * implementation details, contract verification, and auth verification results.
 */
@RestController
@RequestMapping("/api/v1/implementations")
@Slf4j
@RequiredArgsConstructor
public class ImplementationController {

  private final RepoMindService repoMindService;
  private final ProjectService projectService;

  /**
   * Valid operationId pattern: alphanumeric, underscores, hyphens, dots. Prevents path traversal
   * and injection attacks. Examples: "getPetById", "user.create", "orders_list"
   */
  private static final Pattern VALID_OPERATION_ID_PATTERN =
      Pattern.compile("^[a-zA-Z][a-zA-Z0-9_.-]{0,127}$");

  /**
   * Retrieve code intelligence for a specific API operation in a project.
   *
   * @param projectId the project to look up the repository for
   * @param operationId optional OpenAPI operationId to correlate
   * @param path optional HTTP path (e.g. {@code /pets/{id}}) for intelligent correlation
   * @param method optional HTTP method (e.g. {@code GET}) for intelligent correlation
   * @param repositoryPath optional override for the repository path
   * @param principal the authenticated user
   * @return implementation intelligence including source code, contract, and auth verification
   */
  @GetMapping("/projects/{projectId}/operations")
  public Mono<ResponseEntity<ImplementationIntelligenceResponse>> getImplementationIntelligence(
      @PathVariable Long projectId,
      @RequestParam(required = false) String operationId,
      @RequestParam(required = false) String path,
      @RequestParam(required = false) String method,
      @RequestParam(required = false) String repositoryPath,
      @AuthenticationPrincipal CustomOAuth2User principal) {

    // Validate operationId if present
    if (operationId != null && !VALID_OPERATION_ID_PATTERN.matcher(operationId).matches()) {
      log.warn(
          "Invalid operationId attempted: '{}' by user {}", operationId, principal.getUserId());
      throw new ValidationException(
          "Invalid operationId format. Must be alphanumeric with optional underscores, hyphens, or"
              + " dots.");
    }

    log.debug(
        "Fetching intelligence for operationId: '{}' (path: {}, method: {}) in project {}",
        operationId,
        path,
        method,
        projectId);

    // 1. Determine repository context
    String effectiveRepoPath;
    String repoName;

    if (repositoryPath != null && !repositoryPath.isBlank()) {
      effectiveRepoPath = repositoryPath;
      // Derive repo name from path
      String[] segments = repositoryPath.replace("\\", "/").split("/");
      repoName = segments[segments.length - 1];
    } else {
      Project project = projectService.getProject(projectId, principal.getUserId());
      if (project.getRepositoryPath() == null || project.getRepositoryPath().isBlank()) {
        log.debug("No repository linked to project {}", projectId);
        return Mono.just(ResponseEntity.notFound().build());
      }
      effectiveRepoPath = project.getRepositoryPath();
      repoName = project.getName();
    }

    // 2. Step 1: Attempt to intelligently correlate spec to code if path and method are provided
    Mono<String> symbolResolverMono;
    if (path != null && method != null) {
      symbolResolverMono =
          repoMindService
              .intelligentCorrelate(repoName, path, method, operationId)
              .map(
                  correlation ->
                      correlation.matched()
                          ? correlation.best_match().qualified_name()
                          : (operationId != null ? operationId : ""))
              .onErrorResume(
                  e -> {
                    log.warn(
                        "Intelligent correlation failed, falling back to operationId: {}",
                        e.getMessage());
                    return Mono.just(operationId != null ? operationId : "");
                  });
    } else {
      symbolResolverMono = Mono.just(operationId != null ? operationId : "");
    }

    // 3. Step 2 & 3: Resolve implementation and verify contract in parallel
    return symbolResolverMono.flatMap(
        resolvedSymbol -> {
          if (resolvedSymbol == null || resolvedSymbol.isBlank()) {
            log.info(
                "No symbol resolved for path: {} method: {}. Returning empty intelligence.",
                path,
                method);
            String noCodeMsg =
                "// Could not correlate this endpoint to any source code handler.\n"
                    + "// Ensure the repository is indexed and the path/method match"
                    + " your controller.";
            return Mono.just(
                ResponseEntity.ok(
                    new ImplementationIntelligenceResponse(
                        new ImplementationCodeResponse("unknown", noCodeMsg, 0, "text"),
                        new ContractVerificationResponse(
                            false, Collections.emptyList(), "Not analyzed - symbol not found"),
                        new AuthVerificationResponse(false, Collections.emptyList(), "N/A", "N/A"),
                        Collections.emptyList())));
          }

          Mono<ImplementationCodeResponse> codeMono =
              repoMindService.getImplementationCode(repoName, resolvedSymbol);
          Mono<ContractVerificationResponse> contractMono =
              (path != null && method != null)
                  ? repoMindService.verifyContract(repoName, path, method).onErrorReturn(null)
                  : Mono.justOrEmpty(null);
          Mono<AuthVerificationResponse> authMono =
              (path != null && method != null)
                  ? repoMindService
                      .verifyAuthContract(repoName, path, method, Collections.emptyList())
                      .onErrorReturn(null)
                  : Mono.justOrEmpty(null);

          return Mono.zip(
                  codeMono.onErrorResume(
                      e ->
                          Mono.just(
                              new ImplementationCodeResponse(
                                  "unknown",
                                  "// Implementation not found for " + resolvedSymbol,
                                  0,
                                  "text"))),
                  contractMono.defaultIfEmpty(
                      new ContractVerificationResponse(
                          false, Collections.emptyList(), "Not analyzed")),
                  authMono.defaultIfEmpty(
                      new AuthVerificationResponse(false, Collections.emptyList(), "N/A", "N/A")))
              .map(
                  tuple -> {
                    ImplementationCodeResponse code = tuple.getT1();
                    ContractVerificationResponse contract = tuple.getT2();
                    AuthVerificationResponse auth = tuple.getT3();

                    // Extract callStack from best_match if available (requires passing more state
                    // through)
                    List<String> callStack = Collections.emptyList();

                    return ResponseEntity.ok(
                        new ImplementationIntelligenceResponse(code, contract, auth, callStack));
                  });
        });
  }
}
