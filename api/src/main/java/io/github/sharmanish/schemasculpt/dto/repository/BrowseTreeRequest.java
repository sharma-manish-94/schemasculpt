package io.github.sharmanish.schemasculpt.dto.repository;

import jakarta.validation.constraints.NotBlank;

/**
 * Request to browse repository tree.
 *
 * @param owner Repository owner (user or organization)
 * @param repo Repository name
 * @param path Path within the repository (defaults to root "")
 * @param branch Optional branch name
 */
public record BrowseTreeRequest(
    @NotBlank(message = "Repository owner must not be blank") String owner,
    @NotBlank(message = "Repository name must not be blank") String repo,
    String path,
    String branch) {

  /** Canonical constructor with default path value. */
  public BrowseTreeRequest {
    path = path != null ? path : "";
  }
}
