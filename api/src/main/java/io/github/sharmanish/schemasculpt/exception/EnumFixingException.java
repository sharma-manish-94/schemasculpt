package io.github.sharmanish.schemasculpt.exception;

/**
 * Exception thrown when enum fixing operations fail. Maps to HTTP 400 Bad Request.
 */
public final class EnumFixingException extends ClientException {

  public EnumFixingException(String message) {
    super(ErrorCode.ENUM_FIXING_ERROR, message);
  }

  public EnumFixingException(String message, Throwable cause) {
    super(ErrorCode.ENUM_FIXING_ERROR, message, cause);
  }
}
