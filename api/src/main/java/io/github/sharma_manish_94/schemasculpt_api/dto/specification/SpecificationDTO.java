package io.github.sharma_manish_94.schemasculpt_api.dto.specification;

import io.github.sharma_manish_94.schemasculpt_api.entity.Specification;
import java.time.LocalDateTime;

public record SpecificationDTO(
    Long id,
    String version,
    String specFormat,
    String commitMessage,
    Boolean isCurrent,
    LocalDateTime createdAt,
    String createdByUsername) {
  public SpecificationDTO(Specification spec) {
    this(
        spec.getId(),
        spec.getVersion(),
        spec.getSpecFormat(),
        spec.getCommitMessage(),
        spec.getIsCurrent(),
        spec.getCreatedAt(),
        spec.getCreatedBy() != null ? spec.getCreatedBy().getUsername() : null);
  }
}
