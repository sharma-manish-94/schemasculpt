package io.github.sharmanish.schemasculpt.exception;

/**
 * Base exception for external service failures. Indicates that a downstream dependency (AI service,
 * proxy, etc.) is unavailable or returned an error. Maps to HTTP 502.
 */
public sealed class ServiceException extends SchemaSculptException
    permits AIServiceException,
        ProxyServiceException,
        TestGenerationException,
        MockDataGenerationException {

  protected ServiceException(ErrorCode errorCode, String message) {
    super(errorCode, message);
  }

  protected ServiceException(ErrorCode errorCode, String message, Throwable cause) {
    super(errorCode, message, cause);
  }
}
