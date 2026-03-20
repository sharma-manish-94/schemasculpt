package io.github.sharmanish.schemasculpt.exception;

/** Exception thrown when a project cannot be found. Maps to HTTP 404 Not Found. */
public final class ProjectNotFoundException extends ResourceNotFoundException {

  public ProjectNotFoundException(Long projectId) {
    super(ErrorCode.PROJECT_NOT_FOUND, "Project not found with ID: " + projectId);
  }
}
