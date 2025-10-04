package io.github.sharma_manish_94.schemasculpt_api.exception;

public class ForbiddenException extends SchemaSculptException {

    public ForbiddenException(String message) {
        super("FORBIDDEN", message);
    }
}
