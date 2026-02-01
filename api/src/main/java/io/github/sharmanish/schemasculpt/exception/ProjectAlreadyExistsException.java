package io.github.sharmanish.schemasculpt.exception;

/**
 * Exception thrown when attempting to create a project that already exists. Maps to HTTP 409
 * Conflict.
 */
public final class ProjectAlreadyExistsException extends ClientException {

  public ProjectAlreadyExistsException(String projectName) {
    super(
        ErrorCode.PROJECT_ALREADY_EXISTS, "Project with name '" + projectName + "' already exists");
  }
}
