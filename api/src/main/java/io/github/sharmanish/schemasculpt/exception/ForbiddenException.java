package io.github.sharmanish.schemasculpt.exception;

/**
 * Exception thrown when a user lacks permission for an operation. Maps to HTTP 403 Forbidden.
 */
public final class ForbiddenException extends AuthorizationException {

  public ForbiddenException(String message) {
    super(ErrorCode.FORBIDDEN, message);
  }
}
