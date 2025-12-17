package io.github.sharmanish.schemasculpt.dto.project;

import jakarta.validation.constraints.Size;

public record UpdateProjectRequest(
    @Size(max = 255, message = "Project name must not exceed 255 characters") String name,
    @Size(max = 1000, message = "Description must not exceed 1000 characters") String description,
    Boolean isPublic) {
}
