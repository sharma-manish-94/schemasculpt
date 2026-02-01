package io.github.sharmanish.schemasculpt.dto.request;

import jakarta.validation.constraints.NotBlank;

public record LinkRepositoryRequest(
    @NotBlank(message = "Repository path cannot be blank") String path) {}
