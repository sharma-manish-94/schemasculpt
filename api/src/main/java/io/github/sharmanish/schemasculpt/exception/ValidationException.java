package io.github.sharmanish.schemasculpt.exception;

/** Exception thrown when validation operations fail. Maps to HTTP 400 Bad Request. */
public final class ValidationException extends ClientException {

  public ValidationException(String message) {
    super(ErrorCode.VALIDATION_ERROR, message);
  }

  public ValidationException(String message, Throwable cause) {
    super(ErrorCode.VALIDATION_ERROR, message, cause);
  }
}
