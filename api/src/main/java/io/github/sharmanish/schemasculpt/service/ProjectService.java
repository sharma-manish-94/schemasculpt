package io.github.sharmanish.schemasculpt.service;

import io.github.sharmanish.schemasculpt.entity.Project;
import io.github.sharmanish.schemasculpt.entity.User;
import io.github.sharmanish.schemasculpt.exception.ForbiddenException;
import io.github.sharmanish.schemasculpt.exception.ProjectAlreadyExistsException;
import io.github.sharmanish.schemasculpt.exception.ProjectNotFoundException;
import io.github.sharmanish.schemasculpt.exception.UserNotFoundException;
import io.github.sharmanish.schemasculpt.repository.ProjectRepository;
import io.github.sharmanish.schemasculpt.repository.UserRepository;
import java.util.List;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * Service for managing user projects
 */
@SuppressWarnings("checkstyle:SummaryJavadoc")
@Service
@Slf4j
public class ProjectService {

  private final ProjectRepository projectRepository;
  private final UserRepository userRepository;

  @SuppressWarnings("checkstyle:MissingJavadocMethod")
  public ProjectService(ProjectRepository projectRepository, UserRepository userRepository) {
    this.projectRepository = projectRepository;
    this.userRepository = userRepository;
  }

  /**
   * Create a new project for a user
   */
  @Transactional
  public Project createProject(Long userId, String name, String description, Boolean isPublic) {
    log.info("Creating project '{}' for user {}", name, userId);

    User user =
        userRepository.findById(userId).orElseThrow(() -> new UserNotFoundException(userId));

    // Check if project with same name already exists for user
    if (projectRepository.findByUserIdAndName(userId, name).isPresent()) {
      throw new ProjectAlreadyExistsException(name);
    }

    Project project = new Project();
    project.setUser(user);
    project.setName(name);
    project.setDescription(description);
    project.setIsPublic(isPublic != null && isPublic);

    Project savedProject = projectRepository.save(project);
    log.info("Created project with ID: {}", savedProject.getId());

    return savedProject;
  }

  /**
   * Get all projects for a user
   */
  @Transactional(readOnly = true)
  public List<Project> getUserProjects(Long userId) {
    log.debug("Fetching projects for user {}", userId);
    return projectRepository.findByUserIdOrderByCreatedAtDesc(userId);
  }

  /**
   * Update project details
   */
  @Transactional
  public Project updateProject(
      Long projectId, Long userId, String name, String description, Boolean isPublic) {
    log.info("Updating project {} for user {}", projectId, userId);

    Project project = getProject(projectId, userId);

    // Check if new name conflicts with existing project
    if (name != null && !name.equals(project.getName())) {
      if (projectRepository.findByUserIdAndName(userId, name).isPresent()) {
        throw new ProjectAlreadyExistsException(name);
      }
      project.setName(name);
    }

    if (description != null) {
      project.setDescription(description);
    }

    if (isPublic != null) {
      project.setIsPublic(isPublic);
    }

    return projectRepository.save(project);
  }

  /**
   * Get a specific project by ID
   */
  @SuppressWarnings({"checkstyle:Indentation", "checkstyle:FileTabCharacter"})
  @Transactional(readOnly = true)
  public Project getProject(Long projectId, Long userId) {
    log.debug("Fetching project {} for user {}", projectId, userId);

    Project project =
        projectRepository
            .findById(projectId)
            .orElseThrow(() -> new ProjectNotFoundException(projectId));

    if (!project.getUser().getId().equals(userId) && !project.getIsPublic()) {
      throw new ForbiddenException("You don't have access to this project");
    }

    return project;
  }

  /**
   * Delete a project and all its specifications
   */
  @Transactional
  public void deleteProject(Long projectId, Long userId) {
    log.info("Deleting project {} for user {}", projectId, userId);

    Project project = getProject(projectId, userId);
    projectRepository.delete(project);

    log.info("Deleted project {}", projectId);
  }
}
