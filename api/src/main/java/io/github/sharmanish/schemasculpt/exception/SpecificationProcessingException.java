package io.github.sharmanish.schemasculpt.exception;

/** Exception thrown when specification processing fails. Maps to HTTP 400 Bad Request. */
public final class SpecificationProcessingException extends ClientException {

  public SpecificationProcessingException(String message) {
    super(ErrorCode.SPECIFICATION_PROCESSING_ERROR, message);
  }

  public SpecificationProcessingException(String message, Throwable cause) {
    super(ErrorCode.SPECIFICATION_PROCESSING_ERROR, message, cause);
  }
}
