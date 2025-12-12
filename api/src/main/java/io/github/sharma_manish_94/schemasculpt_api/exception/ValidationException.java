package io.github.sharma_manish_94.schemasculpt_api.exception;

/**
 * Exception thrown when validation operations fail.
 */
public class ValidationException extends SchemaSculptException {

  private static final String ERROR_CODE = "VALIDATION_ERROR";

  public ValidationException(String message) {
    super(ERROR_CODE, message);
  }

  public ValidationException(String message, Throwable cause) {
    super(ERROR_CODE, message, cause);
  }
}
