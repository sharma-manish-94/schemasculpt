package io.github.sharma_manish_94.schemasculpt_api.dto.request;

import static io.github.sharma_manish_94.schemasculpt_api.config.ApplicationConstants.MAX_SPEC_SIZE_BYTES;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

/**
 * Request DTO for updating specification content.
 */
public record UpdateSpecRequest(
    @NotBlank(message = "Specification text cannot be blank")
    @Size(max = MAX_SPEC_SIZE_BYTES, message = "Specification size cannot exceed 5MB")
    String specText) {
}
