package io.github.sharmanish.schemasculpt.controller.project;

import io.github.sharmanish.schemasculpt.dto.project.CreateProjectRequest;
import io.github.sharmanish.schemasculpt.dto.project.ProjectDTO;
import io.github.sharmanish.schemasculpt.dto.project.UpdateProjectRequest;
import io.github.sharmanish.schemasculpt.entity.Project;
import io.github.sharmanish.schemasculpt.security.CustomOAuth2User;
import io.github.sharmanish.schemasculpt.service.ProjectService;
import io.github.sharmanish.schemasculpt.util.LogSanitizer;
import jakarta.validation.Valid;
import java.util.List;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/projects")
@Slf4j
public class ProjectController {

  private final ProjectService projectService;

  public ProjectController(ProjectService projectService) {
    this.projectService = projectService;
  }

  /**
   * Create a new project
   */
  @PostMapping
  public ResponseEntity<ProjectDTO> createProject(
      @AuthenticationPrincipal CustomOAuth2User principal,
      @Valid @RequestBody CreateProjectRequest request) {

    log.info("Creating project '{}' for user {}", LogSanitizer.sanitize(request.name()), LogSanitizer.sanitize(principal.getUserId()));

    Project project =
        projectService.createProject(
            principal.getUserId(), request.name(), request.description(), request.isPublic());

    return ResponseEntity.status(HttpStatus.CREATED).body(new ProjectDTO(project));
  }

  /**
   * Get all projects for the authenticated user
   */
  @GetMapping
  public ResponseEntity<List<ProjectDTO>> getUserProjects(
      @AuthenticationPrincipal CustomOAuth2User principal) {

    log.debug("Fetching projects for user {}", LogSanitizer.sanitize(principal.getUserId()));

    List<ProjectDTO> projects =
        projectService.getUserProjects(principal.getUserId()).stream()
            .map(ProjectDTO::new)
            .toList();

    return ResponseEntity.ok(projects);
  }

  /**
   * Get a specific project
   */
  @GetMapping("/{projectId}")
  public ResponseEntity<ProjectDTO> getProject(
      @AuthenticationPrincipal CustomOAuth2User principal, @PathVariable Long projectId) {

    log.debug("Fetching project {} for user {}", LogSanitizer.sanitize(projectId), LogSanitizer.sanitize(principal.getUserId()));

    Project project = projectService.getProject(projectId, principal.getUserId());
    return ResponseEntity.ok(new ProjectDTO(project));
  }

  /**
   * Update a project
   */
  @PutMapping("/{projectId}")
  public ResponseEntity<ProjectDTO> updateProject(
      @AuthenticationPrincipal CustomOAuth2User principal,
      @PathVariable Long projectId,
      @Valid @RequestBody UpdateProjectRequest request) {

    log.info("Updating project {} for user {}", LogSanitizer.sanitize(projectId), LogSanitizer.sanitize(principal.getUserId()));

    Project project =
        projectService.updateProject(
            projectId,
            principal.getUserId(),
            request.name(),
            request.description(),
            request.isPublic());

    return ResponseEntity.ok(new ProjectDTO(project));
  }

  /**
   * Delete a project
   */
  @DeleteMapping("/{projectId}")
  public ResponseEntity<Void> deleteProject(
      @AuthenticationPrincipal CustomOAuth2User principal, @PathVariable Long projectId) {

    log.info("Deleting project {} for user {}", LogSanitizer.sanitize(projectId), LogSanitizer.sanitize(principal.getUserId()));

    projectService.deleteProject(projectId, principal.getUserId());
    return ResponseEntity.noContent().build();
  }
}
