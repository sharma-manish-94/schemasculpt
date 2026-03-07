package io.github.sharmanish.schemasculpt.controller;

import io.github.sharmanish.schemasculpt.dto.response.ImplementationCodeResponse;
import io.github.sharmanish.schemasculpt.entity.Project;
import io.github.sharmanish.schemasculpt.exception.ValidationException;
import io.github.sharmanish.schemasculpt.security.CustomOAuth2User;
import io.github.sharmanish.schemasculpt.service.ProjectService;
import io.github.sharmanish.schemasculpt.service.RepoMindService;
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

  @GetMapping("/projects/{projectId}/operations")
  public Mono<ResponseEntity<ImplementationCodeResponse>> getImplementationForOperation(
      @PathVariable Long projectId,
      @RequestParam String operationId,
      @AuthenticationPrincipal CustomOAuth2User principal) {

    // Validate operationId to prevent path traversal and injection attacks
    if (operationId == null || !VALID_OPERATION_ID_PATTERN.matcher(operationId).matches()) {
      log.warn(
          "Invalid operationId attempted: '{}' by user {}", operationId, principal.getUserId());
      throw new ValidationException(
          "Invalid operationId format. Must be alphanumeric with optional underscores, hyphens, or"
              + " dots.");
    }

    log.debug(
        "Fetching implementation for operationId: '{}' in project {}", operationId, projectId);

    // 1. Get project details to find the repository name and verify access
    Project project = projectService.getProject(projectId, principal.getUserId());
    String repoName = project.getName();

    if (project.getRepositoryPath() == null || project.getRepositoryPath().isBlank()) {
      log.debug("No repository linked to project {}", projectId);
      return Mono.just(ResponseEntity.notFound().build());
    }

    // 2. Call RepoMindService to get the implementation code
    return repoMindService
        .getImplementationCode(repoName, operationId)
        .map(ResponseEntity::ok)
        .onErrorResume(
            e -> {
              log.error(
                  "Failed to get implementation for operationId '{}' in project {}: {}",
                  operationId,
                  projectId,
                  e.getMessage());
              return Mono.just(ResponseEntity.internalServerError().build());
            });
  }
}
