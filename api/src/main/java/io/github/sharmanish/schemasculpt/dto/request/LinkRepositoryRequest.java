package io.github.sharmanish.schemasculpt.dto.request;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

/**
 * Request to link a source code repository to a project.
 *
 * @param path Absolute path to the repository. Must be a valid path without path traversal
 *     sequences (like "../").
 */
public record LinkRepositoryRequest(
    @NotBlank(message = "Repository path cannot be blank")
        @Size(max = 1024, message = "Repository path must be at most 1024 characters")
        String path) {

  /**
   * Validates that the path is safe and doesn't contain path traversal sequences.
   *
   * @return true if the path is safe, false otherwise
   */
  public boolean isSafePath() {
    if (path == null || path.isBlank()) {
      return false;
    }
    // Normalize path separators for consistent checking
    String normalizedPath = path.replace("\\", "/");

    // Check for path traversal sequences
    if (normalizedPath.contains("../")
        || normalizedPath.contains("/./")
        || normalizedPath.contains("//")
        || normalizedPath.startsWith("./")
        || normalizedPath.endsWith("/.")
        || normalizedPath.equals("..")) {
      return false;
    }

    // Path should be absolute (Unix or Windows)
    boolean isUnixAbsolute = path.startsWith("/");
    boolean isWindowsAbsolute =
        path.length() >= 3 && path.charAt(1) == ':' && path.charAt(2) == '\\';

    return isUnixAbsolute || isWindowsAbsolute;
  }
}
