package io.github.sharma_manish_94.schemasculpt_api.controller.project;

import io.github.sharma_manish_94.schemasculpt_api.dto.project.CreateProjectRequest;
import io.github.sharma_manish_94.schemasculpt_api.dto.project.ProjectDTO;
import io.github.sharma_manish_94.schemasculpt_api.dto.project.UpdateProjectRequest;
import io.github.sharma_manish_94.schemasculpt_api.entity.Project;
import io.github.sharma_manish_94.schemasculpt_api.security.CustomOAuth2User;
import io.github.sharma_manish_94.schemasculpt_api.service.ProjectService;
import jakarta.validation.Valid;
import java.util.List;
import java.util.stream.Collectors;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

/** REST controller for project management */
@RestController
@RequestMapping("/api/v1/projects")
@Slf4j
public class ProjectController {

  private final ProjectService projectService;

  public ProjectController(ProjectService projectService) {
    this.projectService = projectService;
  }

  /** Create a new project */
  @PostMapping
  public ResponseEntity<ProjectDTO> createProject(
      @AuthenticationPrincipal CustomOAuth2User principal,
      @Valid @RequestBody CreateProjectRequest request) {

    log.info("Creating project '{}' for user {}", request.name(), principal.getUserId());

    Project project =
        projectService.createProject(
            principal.getUserId(), request.name(), request.description(), request.isPublic());

    return ResponseEntity.status(HttpStatus.CREATED).body(new ProjectDTO(project));
  }

  /** Get all projects for the authenticated user */
  @GetMapping
  public ResponseEntity<List<ProjectDTO>> getUserProjects(
      @AuthenticationPrincipal CustomOAuth2User principal) {

    log.debug("Fetching projects for user {}", principal.getUserId());

    List<ProjectDTO> projects =
        projectService.getUserProjects(principal.getUserId()).stream()
            .map(ProjectDTO::new)
            .collect(Collectors.toList());

    return ResponseEntity.ok(projects);
  }

  /** Get a specific project */
  @GetMapping("/{projectId}")
  public ResponseEntity<ProjectDTO> getProject(
      @AuthenticationPrincipal CustomOAuth2User principal, @PathVariable Long projectId) {

    log.debug("Fetching project {} for user {}", projectId, principal.getUserId());

    Project project = projectService.getProject(projectId, principal.getUserId());
    return ResponseEntity.ok(new ProjectDTO(project));
  }

  /** Update a project */
  @PutMapping("/{projectId}")
  public ResponseEntity<ProjectDTO> updateProject(
      @AuthenticationPrincipal CustomOAuth2User principal,
      @PathVariable Long projectId,
      @Valid @RequestBody UpdateProjectRequest request) {

    log.info("Updating project {} for user {}", projectId, principal.getUserId());

    Project project =
        projectService.updateProject(
            projectId,
            principal.getUserId(),
            request.name(),
            request.description(),
            request.isPublic());

    return ResponseEntity.ok(new ProjectDTO(project));
  }

  /** Delete a project */
  @DeleteMapping("/{projectId}")
  public ResponseEntity<Void> deleteProject(
      @AuthenticationPrincipal CustomOAuth2User principal, @PathVariable Long projectId) {

    log.info("Deleting project {} for user {}", projectId, principal.getUserId());

    projectService.deleteProject(projectId, principal.getUserId());
    return ResponseEntity.noContent().build();
  }
}
