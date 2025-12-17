package io.github.sharmanish.schemasculpt.dto.specification;

import jakarta.validation.constraints.NotBlank;

public record SaveSpecificationRequest(
    @NotBlank(message = "Specification content is required") String specContent,
    String specFormat, // json or yaml
    String commitMessage) {
}
