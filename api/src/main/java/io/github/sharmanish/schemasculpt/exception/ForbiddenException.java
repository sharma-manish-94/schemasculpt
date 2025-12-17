package io.github.sharmanish.schemasculpt.exception;

public class ForbiddenException extends SchemaSculptException {

  public ForbiddenException(String message) {
    super("FORBIDDEN", message);
  }
}
