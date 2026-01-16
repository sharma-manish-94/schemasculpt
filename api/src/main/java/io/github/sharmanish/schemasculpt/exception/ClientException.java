package io.github.sharmanish.schemasculpt.exception;

/**
 * Base exception for client-side errors: invalid input, validation failures, or conflicting state.
 * Maps to HTTP 400 or 409.
 */
public sealed class ClientException extends SchemaSculptException
    permits InvalidSpecificationException, ValidationException, ProjectAlreadyExistsException {

  protected ClientException(ErrorCode errorCode, String message) {
    super(errorCode, message);
  }

  protected ClientException(ErrorCode errorCode, String message, Throwable cause) {
    super(errorCode, message, cause);
  }
}
