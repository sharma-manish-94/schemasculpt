package io.github.sharmanish.schemasculpt.exception;

public class ProjectNotFoundException extends SchemaSculptException {

  public ProjectNotFoundException(Long projectId) {
    super("PROJECT_NOT_FOUND", "Project not found with ID: " + projectId);
  }
}
