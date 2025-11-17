package io.github.sharma_manish_94.schemasculpt_api.dto.project;

import io.github.sharma_manish_94.schemasculpt_api.entity.Project;
import java.time.LocalDateTime;

public record ProjectDTO(
    Long id,
    String name,
    String description,
    Boolean isPublic,
    LocalDateTime createdAt,
    LocalDateTime updatedAt,
    Integer specificationCount) {
  public ProjectDTO(Project project) {
    this(
        project.getId(),
        project.getName(),
        project.getDescription(),
        project.getIsPublic(),
        project.getCreatedAt(),
        project.getUpdatedAt(),
        project.getSpecifications() != null ? project.getSpecifications().size() : 0);
  }
}
