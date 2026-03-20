package io.github.sharmanish.schemasculpt.exception;

/**
 * Base exception for authorization failures. The user is authenticated but lacks permission. Maps
 * to HTTP 403.
 */
public sealed class AuthorizationException extends SchemaSculptException
    permits ForbiddenException {

  protected AuthorizationException(ErrorCode errorCode, String message) {
    super(errorCode, message);
  }
}
