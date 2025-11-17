package io.github.sharma_manish_94.schemasculpt_api.exception;

public class ProjectNotFoundException extends SchemaSculptException {

  public ProjectNotFoundException(Long projectId) {
    super("PROJECT_NOT_FOUND", "Project not found with ID: " + projectId);
  }
}
