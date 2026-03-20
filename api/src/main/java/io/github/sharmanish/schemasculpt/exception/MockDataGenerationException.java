package io.github.sharmanish.schemasculpt.exception;

/** Exception thrown when mock data generation fails. Maps to HTTP 502 Bad Gateway. */
public final class MockDataGenerationException extends ServiceException {

  public MockDataGenerationException(String message) {
    super(ErrorCode.MOCK_DATA_GENERATION_ERROR, message);
  }

  public MockDataGenerationException(String message, Throwable cause) {
    super(ErrorCode.MOCK_DATA_GENERATION_ERROR, message, cause);
  }
}
