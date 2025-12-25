package io.github.sharmanish.schemasculpt.dto.request;

import static io.github.sharmanish.schemasculpt.config.ApplicationConstants.MAX_SPEC_SIZE_BYTES;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

/** Request DTO for creating a new session. */
public record CreateSessionRequest(
    @NotBlank(message = "Specification text cannot be blank")
        @Size(max = MAX_SPEC_SIZE_BYTES, message = "Specification size cannot exceed 5MB")
        String specText) {}
