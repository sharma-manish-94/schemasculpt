package io.github.sharmanish.schemasculpt.exception;

/**
 * Exception thrown when test case generation fails. Maps to HTTP 502 Bad Gateway.
 */
public final class TestGenerationException extends ServiceException {

  public TestGenerationException(String message) {
    super(ErrorCode.TEST_GENERATION_ERROR, message);
  }

  public TestGenerationException(String message, Throwable cause) {
    super(ErrorCode.TEST_GENERATION_ERROR, message, cause);
  }
}
