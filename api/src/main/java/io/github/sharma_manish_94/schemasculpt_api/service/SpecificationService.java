package io.github.sharma_manish_94.schemasculpt_api.service;

import io.github.sharma_manish_94.schemasculpt_api.entity.Project;
import io.github.sharma_manish_94.schemasculpt_api.entity.Specification;
import io.github.sharma_manish_94.schemasculpt_api.entity.User;
import io.github.sharma_manish_94.schemasculpt_api.exception.ForbiddenException;
import io.github.sharma_manish_94.schemasculpt_api.exception.ProjectNotFoundException;
import io.github.sharma_manish_94.schemasculpt_api.exception.SpecificationNotFoundException;
import io.github.sharma_manish_94.schemasculpt_api.exception.UserNotFoundException;
import io.github.sharma_manish_94.schemasculpt_api.repository.ProjectRepository;
import io.github.sharma_manish_94.schemasculpt_api.repository.SpecificationRepository;
import io.github.sharma_manish_94.schemasculpt_api.repository.UserRepository;
import java.util.List;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * Service for managing specification versions
 */
@Service
@Slf4j
public class SpecificationService {

  private final SpecificationRepository specificationRepository;
  private final ProjectRepository projectRepository;
  private final UserRepository userRepository;

  public SpecificationService(
      SpecificationRepository specificationRepository,
      ProjectRepository projectRepository,
      UserRepository userRepository) {
    this.specificationRepository = specificationRepository;
    this.projectRepository = projectRepository;
    this.userRepository = userRepository;
  }

  /**
   * Get the current version of a specification
   */
  @Transactional(readOnly = true)
  public Specification getCurrentSpecification(Long projectId, Long userId) {
    log.debug("Fetching current specification for project {}", projectId);

    // Verify project access
    Project project =
        projectRepository
            .findById(projectId)
            .orElseThrow(() -> new ProjectNotFoundException(projectId));

    if (!project.getUser().getId().equals(userId)) {
      throw new ForbiddenException("You don't have access to this project");
    }

    return specificationRepository.findByProjectIdAndIsCurrentTrue(projectId).orElse(null);
  }

  /**
   * Get all versions of a specification
   */
  @Transactional(readOnly = true)
  public List<Specification> getSpecificationVersions(Long projectId, Long userId) {
    log.debug("Fetching all specification versions for project {}", projectId);

    // Verify project access
    Project project =
        projectRepository
            .findById(projectId)
            .orElseThrow(() -> new ProjectNotFoundException(projectId));

    if (!project.getUser().getId().equals(userId)) {
      throw new ForbiddenException("You don't have access to this project");
    }

    return specificationRepository.findByProjectIdOrderByCreatedAtDesc(projectId);
  }

  /**
   * Revert to a previous version
   */
  @Transactional
  public Specification revertToVersion(
      Long projectId, String version, Long userId, String commitMessage) {
    log.info("Reverting project {} to version {}", projectId, version);

    // Get the version to revert to
    Specification targetSpec = getSpecificationByVersion(projectId, version, userId);

    // Create a new version based on the old content
    String revertMessage = commitMessage != null ? commitMessage : "Reverted to version " + version;

    return saveSpecification(
        projectId, userId, targetSpec.getSpecContent(), targetSpec.getSpecFormat(), revertMessage);
  }

  /**
   * Get a specific version of a specification
   */
  @Transactional(readOnly = true)
  public Specification getSpecificationByVersion(Long projectId, String version, Long userId) {
    log.debug("Fetching specification version {} for project {}", version, projectId);

    // Verify project access
    Project project =
        projectRepository
            .findById(projectId)
            .orElseThrow(() -> new ProjectNotFoundException(projectId));

    if (!project.getUser().getId().equals(userId)) {
      throw new ForbiddenException("You don't have access to this project");
    }

    return specificationRepository
        .findByProjectIdAndVersion(projectId, version)
        .orElseThrow(() -> new SpecificationNotFoundException(version));
  }

  /**
   * Save a new version of a specification
   */
  @Transactional
  public Specification saveSpecification(
      Long projectId, Long userId, String specContent, String specFormat, String commitMessage) {

    log.info("Saving new specification version for project {}", projectId);

    // Verify project access
    Project project =
        projectRepository
            .findById(projectId)
            .orElseThrow(() -> new ProjectNotFoundException(projectId));

    if (!project.getUser().getId().equals(userId)) {
      throw new ForbiddenException("You don't have access to this project");
    }

    User user =
        userRepository.findById(userId).orElseThrow(() -> new UserNotFoundException(userId));

    // Mark all previous versions as not current
    List<Specification> existingSpecs =
        specificationRepository.findByProjectIdOrderByCreatedAtDesc(projectId);

    existingSpecs.forEach(spec -> spec.setIsCurrent(false));
    specificationRepository.saveAll(existingSpecs);

    // Generate version number
    String version = generateVersionNumber(existingSpecs.size() + 1);

    // Create new specification
    Specification specification = new Specification();
    specification.setProject(project);
    specification.setVersion(version);
    specification.setSpecContent(specContent);
    specification.setSpecFormat(specFormat != null ? specFormat : "json");
    specification.setCommitMessage(commitMessage);
    specification.setIsCurrent(true);
    specification.setCreatedBy(user);

    Specification saved = specificationRepository.save(specification);
    log.info("Saved specification version {} with ID: {}", version, saved.getId());

    return saved;
  }

  /**
   * Generate version number in format v1, v2, v3, etc.
   */
  private String generateVersionNumber(int versionNum) {
    return "v" + versionNum;
  }
}
