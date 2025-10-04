package io.github.sharma_manish_94.schemasculpt_api.exception;

public class ProjectAlreadyExistsException extends SchemaSculptException {

    public ProjectAlreadyExistsException(String projectName) {
        super("PROJECT_ALREADY_EXISTS", "Project with name '" + projectName + "' already exists");
    }
}
