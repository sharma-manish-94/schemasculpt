package io.github.sharmanish.schemasculpt.dto.project;

import io.github.sharmanish.schemasculpt.entity.Project;
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
