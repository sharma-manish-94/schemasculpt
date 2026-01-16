package io.github.sharmanish.schemasculpt.exception;

import org.springframework.http.HttpStatus;

/**
 * Standardized error codes for SchemaSculpt exceptions. Each code maps to an HTTP status and
 * provides a machine-readable identifier for client error handling.
 */
public enum ErrorCode {
  // Resource not found (404)
  PROJECT_NOT_FOUND(HttpStatus.NOT_FOUND),
  SPECIFICATION_NOT_FOUND(HttpStatus.NOT_FOUND),
  SESSION_NOT_FOUND(HttpStatus.NOT_FOUND),
  USER_NOT_FOUND(HttpStatus.NOT_FOUND),

  // Client errors (400)
  INVALID_SPECIFICATION(HttpStatus.BAD_REQUEST),
  VALIDATION_ERROR(HttpStatus.BAD_REQUEST),
  PROJECT_ALREADY_EXISTS(HttpStatus.CONFLICT),

  // Authorization errors (403)
  FORBIDDEN(HttpStatus.FORBIDDEN),

  // Service errors (502/503)
  AI_SERVICE_ERROR(HttpStatus.BAD_GATEWAY),
  PROXY_SERVICE_ERROR(HttpStatus.BAD_GATEWAY);

  private final HttpStatus httpStatus;

  ErrorCode(HttpStatus httpStatus) {
    this.httpStatus = httpStatus;
  }

  public HttpStatus httpStatus() {
    return httpStatus;
  }

  public String code() {
    return name();
  }
}
