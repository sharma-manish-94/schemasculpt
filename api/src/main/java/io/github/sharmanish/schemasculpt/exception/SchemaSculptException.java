package io.github.sharmanish.schemasculpt.exception;

import org.springframework.http.HttpStatus;

/**
 * Base exception class for SchemaSculpt application. All custom exceptions should extend this
 * class.
 *
 * <p>This class uses sealed types to create a type-safe exception hierarchy:
 *
 * <pre>
 * SchemaSculptException (abstract)
 * ├── AuthorizationException (sealed) → ForbiddenException
 * ├── ResourceNotFoundException (sealed) → Project/Specification/Session/UserNotFoundException
 * ├── ClientException (sealed) → InvalidSpecification/Validation/ProjectAlreadyExistsException
 * └── ServiceException (sealed) → AIService/ProxyServiceException
 * </pre>
 */
public abstract class SchemaSculptException extends RuntimeException {

  private final ErrorCode errorCode;

  protected SchemaSculptException(ErrorCode errorCode, String message) {
    super(message);
    this.errorCode = errorCode;
  }

  protected SchemaSculptException(ErrorCode errorCode, String message, Throwable cause) {
    super(message, cause);
    this.errorCode = errorCode;
  }

  public ErrorCode getErrorCode() {
    return errorCode;
  }

  /** Returns the error code as a string for API responses. */
  public String getErrorCodeString() {
    return errorCode.code();
  }

  /** Returns the HTTP status associated with this exception. */
  public HttpStatus getHttpStatus() {
    return errorCode.httpStatus();
  }
}
