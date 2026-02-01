package io.github.sharmanish.schemasculpt.exception;

import io.github.sharmanish.schemasculpt.dto.ErrorResponse;
import java.util.stream.Collectors;
import lombok.extern.slf4j.Slf4j;
import org.springframework.context.support.DefaultMessageSourceResolvable;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ControllerAdvice;
import org.springframework.web.bind.annotation.ExceptionHandler;

/**
 * Global exception handler using sealed class hierarchy for type-safe exception handling.
 *
 * <p>Exception hierarchy:
 *
 * <ul>
 *   <li>{@link AuthorizationException} → HTTP 403 (Forbidden)
 *   <li>{@link ResourceNotFoundException} → HTTP 404 (Not Found)
 *   <li>{@link ClientException} → HTTP 400/409 (Bad Request/Conflict)
 *   <li>{@link ServiceException} → HTTP 502 (Bad Gateway)
 * </ul>
 */
@ControllerAdvice
@Slf4j
public class GlobalExceptionHandler {

  /** Handles authorization failures (user lacks permission). Maps to HTTP 403 Forbidden. */
  @ExceptionHandler(AuthorizationException.class)
  public ResponseEntity<ErrorResponse> handleAuthorization(AuthorizationException e) {
    log.warn("Authorization failure: {}", e.getMessage());
    return ResponseEntity.status(e.getHttpStatus())
        .body(new ErrorResponse(e.getErrorCodeString(), e.getMessage()));
  }

  /** Handles resource not found errors. Maps to HTTP 404 Not Found. */
  @ExceptionHandler(ResourceNotFoundException.class)
  public ResponseEntity<ErrorResponse> handleResourceNotFound(ResourceNotFoundException e) {
    log.warn("Resource not found: {}", e.getMessage());
    return ResponseEntity.status(e.getHttpStatus())
        .body(new ErrorResponse(e.getErrorCodeString(), e.getMessage()));
  }

  /** Handles client errors (invalid input, validation failures). Maps to HTTP 400 or 409. */
  @ExceptionHandler(ClientException.class)
  public ResponseEntity<ErrorResponse> handleClientError(ClientException e) {
    log.warn("Client error: {}", e.getMessage());
    return ResponseEntity.status(e.getHttpStatus())
        .body(new ErrorResponse(e.getErrorCodeString(), e.getMessage()));
  }

  /** Handles external service failures (AI service, proxy). Maps to HTTP 502 Bad Gateway. */
  @ExceptionHandler(ServiceException.class)
  public ResponseEntity<ErrorResponse> handleServiceError(ServiceException e) {
    log.error("Service error: {}", e.getMessage(), e);
    return ResponseEntity.status(e.getHttpStatus())
        .body(new ErrorResponse(e.getErrorCodeString(), e.getMessage()));
  }

  /** Handles Spring validation errors from @Valid annotations. */
  @ExceptionHandler(MethodArgumentNotValidException.class)
  public ResponseEntity<ErrorResponse> handleValidation(MethodArgumentNotValidException e) {
    String message =
        e.getBindingResult().getAllErrors().stream()
            .map(DefaultMessageSourceResolvable::getDefaultMessage)
            .collect(Collectors.joining(", "));
    return ResponseEntity.badRequest()
        .body(new ErrorResponse(ErrorCode.VALIDATION_ERROR.code(), message));
  }

  /** Handles illegal argument exceptions. */
  @ExceptionHandler(IllegalArgumentException.class)
  public ResponseEntity<ErrorResponse> handleIllegalArgument(IllegalArgumentException e) {
    log.warn("Invalid argument: {}", e.getMessage());
    return ResponseEntity.badRequest().body(new ErrorResponse("INVALID_ARGUMENT", e.getMessage()));
  }

  /** Handles Java security exceptions. */
  @ExceptionHandler(SecurityException.class)
  public ResponseEntity<ErrorResponse> handleSecurity(SecurityException e) {
    log.warn("Security violation: {}", e.getMessage());
    return ResponseEntity.status(HttpStatus.FORBIDDEN)
        .body(new ErrorResponse(ErrorCode.FORBIDDEN.code(), "Access denied"));
  }

  /** Fallback handler for unexpected exceptions. */
  @ExceptionHandler(Exception.class)
  public ResponseEntity<ErrorResponse> handleGeneral(Exception e) {
    log.error("Unexpected error occurred", e);
    return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
        .body(new ErrorResponse("INTERNAL_ERROR", "An unexpected error occurred"));
  }
}
