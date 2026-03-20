package io.github.sharmanish.schemasculpt.exception;

/** Exception thrown when AI service operations fail. Maps to HTTP 502 Bad Gateway. */
public final class AIServiceException extends ServiceException {

  public AIServiceException(String message) {
    super(ErrorCode.AI_SERVICE_ERROR, message);
  }

  public AIServiceException(String message, Throwable cause) {
    super(ErrorCode.AI_SERVICE_ERROR, message, cause);
  }
}
