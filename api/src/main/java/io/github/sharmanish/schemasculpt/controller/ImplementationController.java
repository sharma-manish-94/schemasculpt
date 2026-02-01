package io.github.sharmanish.schemasculpt.controller;

import io.github.sharmanish.schemasculpt.dto.response.ImplementationCodeResponse;
import io.github.sharmanish.schemasculpt.entity.Project;
import io.github.sharmanish.schemasculpt.security.CustomOAuth2User;
import io.github.sharmanish.schemasculpt.service.ProjectService;
import io.github.sharmanish.schemasculpt.service.RepoMindService;
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

  @GetMapping("/projects/{projectId}/operations")
  public Mono<ResponseEntity<ImplementationCodeResponse>> getImplementationForOperation(
      @PathVariable Long projectId,
      @RequestParam String operationId,
      @AuthenticationPrincipal CustomOAuth2User principal) {

    log.debug(
        "Fetching implementation for operationId: '{}' in project {}", operationId, projectId);

    // 1. Get project details to find the repository name and verify access
    Project project = projectService.getProject(projectId, principal.getUserId());
    String repoName = project.getName(); // Assuming project name is used as repo name in RepoMind

    if (project.getRepositoryPath() == null || project.getRepositoryPath().isBlank()) {
      return Mono.just(ResponseEntity.notFound().build());
    }

    // 2. Call RepoMindService to get the implementation code
    return repoMindService
        .getImplementationCode(repoName, operationId)
        .map(ResponseEntity::ok)
        .onErrorResume(
            e -> {
              log.error("Failed to get implementation for {}", operationId, e);
              return Mono.just(ResponseEntity.status(500).build());
            });
  }
}
