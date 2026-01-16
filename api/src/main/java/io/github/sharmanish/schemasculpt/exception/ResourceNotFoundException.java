package io.github.sharmanish.schemasculpt.exception;

/**
 * Base exception for all resource-not-found scenarios. Maps to HTTP 404.
 *
 * <p>Permitted subclasses cover specific resource types to enable pattern matching in exception
 * handlers.
 */
public sealed class ResourceNotFoundException extends SchemaSculptException
    permits ProjectNotFoundException,
        SpecificationNotFoundException,
        SessionNotFoundException,
        UserNotFoundException {

  protected ResourceNotFoundException(ErrorCode errorCode, String message) {
    super(errorCode, message);
  }

  protected ResourceNotFoundException(ErrorCode errorCode, String message, Throwable cause) {
    super(errorCode, message, cause);
  }
}
