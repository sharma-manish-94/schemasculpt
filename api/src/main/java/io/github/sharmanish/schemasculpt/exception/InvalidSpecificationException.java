package io.github.sharmanish.schemasculpt.exception;

/**
 * Exception thrown when an OpenAPI specification is invalid or malformed. Maps to HTTP 400 Bad
 * Request.
 */
public final class InvalidSpecificationException extends ClientException {

  public InvalidSpecificationException(String message) {
    super(ErrorCode.INVALID_SPECIFICATION, message);
  }

  public InvalidSpecificationException(String message, Throwable cause) {
    super(ErrorCode.INVALID_SPECIFICATION, message, cause);
  }
}
