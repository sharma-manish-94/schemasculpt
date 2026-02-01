package io.github.sharmanish.schemasculpt.exception;

/** Exception thrown when a session cannot be found. Maps to HTTP 404 Not Found. */
public final class SessionNotFoundException extends ResourceNotFoundException {

  public SessionNotFoundException(String sessionId) {
    super(ErrorCode.SESSION_NOT_FOUND, "Session not found: " + sessionId);
  }

  public SessionNotFoundException(String sessionId, Throwable cause) {
    super(ErrorCode.SESSION_NOT_FOUND, "Session not found: " + sessionId, cause);
  }
}
