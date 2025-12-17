package io.github.sharmanish.schemasculpt.dto.specification;

import io.github.sharmanish.schemasculpt.entity.Specification;
import java.time.LocalDateTime;

public record SpecificationDetailDTO(
    Long id,
    String version,
    String specContent,
    String specFormat,
    String commitMessage,
    Boolean isCurrent,
    LocalDateTime createdAt,
    String createdByUsername) {
  public SpecificationDetailDTO(Specification spec) {
    this(
        spec.getId(),
        spec.getVersion(),
        spec.getSpecContent(),
        spec.getSpecFormat(),
        spec.getCommitMessage(),
        spec.getIsCurrent(),
        spec.getCreatedAt(),
        spec.getCreatedBy() != null ? spec.getCreatedBy().getUsername() : null);
  }
}
