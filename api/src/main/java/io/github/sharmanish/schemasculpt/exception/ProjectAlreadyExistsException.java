package io.github.sharmanish.schemasculpt.exception;

public class ProjectAlreadyExistsException extends SchemaSculptException {

  public ProjectAlreadyExistsException(String projectName) {
    super("PROJECT_ALREADY_EXISTS", "Project with name '" + projectName + "' already exists");
  }
}
