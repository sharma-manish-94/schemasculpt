package io.github.sharmanish.schemasculpt.dto.repository;

import jakarta.validation.constraints.NotBlank;

/**
 * Request to read a file from repository.
 *
 * @param owner Repository owner (user or organization)
 * @param repo  Repository name
 * @param path  Path to the file within the repository
 * @param ref   Optional branch, tag, or commit SHA (defaults to default branch)
 */
public record ReadFileRequest(
    @NotBlank(message = "Repository owner must not be blank") String owner,
    @NotBlank(message = "Repository name must not be blank") String repo,
    @NotBlank(message = "File path must not be blank") String path,
    String ref) {}
