package io.github.sharma_manish_94.schemasculpt_api.exception;

/** Exception thrown when an OpenAPI specification is invalid or malformed. */
public class InvalidSpecificationException extends SchemaSculptException {

  private static final String ERROR_CODE = "INVALID_SPECIFICATION";

  public InvalidSpecificationException(String message) {
    super(ERROR_CODE, message);
  }

  public InvalidSpecificationException(String message, Throwable cause) {
    super(ERROR_CODE, message, cause);
  }
}
