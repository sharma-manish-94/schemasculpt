package io.github.sharma_manish_94.schemasculpt_api.exception;

import io.github.sharma_manish_94.schemasculpt_api.dto.ErrorResponse;
import java.util.stream.Collectors;
import lombok.extern.slf4j.Slf4j;
import org.springframework.context.support.DefaultMessageSourceResolvable;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ControllerAdvice;
import org.springframework.web.bind.annotation.ExceptionHandler;

@ControllerAdvice
@Slf4j
public class GlobalExceptionHandler {
  @ExceptionHandler(InvalidSpecificationException.class)
  public ResponseEntity<ErrorResponse> handleInvalidSpec(InvalidSpecificationException e) {
    log.warn("Invalid specification: {}", e.getMessage());
    ErrorResponse errorResponse = new ErrorResponse("INVALID_SPECIFICATION", e.getMessage());
    return ResponseEntity.badRequest().body(errorResponse);
  }

  @ExceptionHandler(SessionNotFoundException.class)
  public ResponseEntity<ErrorResponse> handleSessionNotFound(SessionNotFoundException e) {
    log.warn("Session not found: {}", e.getMessage());
    return ResponseEntity.status(HttpStatus.NOT_FOUND)
        .body(new ErrorResponse("SESSION_NOT_FOUND", e.getMessage()));
  }

  @ExceptionHandler(MethodArgumentNotValidException.class)
  public ResponseEntity<ErrorResponse> handleValidation(MethodArgumentNotValidException e) {
    String message =
        e.getBindingResult().getAllErrors().stream()
            .map(DefaultMessageSourceResolvable::getDefaultMessage)
            .collect(Collectors.joining(", "));
    return ResponseEntity.badRequest().body(new ErrorResponse("VALIDATION_ERROR", message));
  }

  @ExceptionHandler(IllegalArgumentException.class)
  public ResponseEntity<ErrorResponse> handleIllegalArgument(IllegalArgumentException e) {
    log.warn("Invalid argument: {}", e.getMessage());
    return ResponseEntity.badRequest().body(new ErrorResponse("INVALID_ARGUMENT", e.getMessage()));
  }

  @ExceptionHandler(SecurityException.class)
  public ResponseEntity<ErrorResponse> handleSecurity(SecurityException e) {
    log.warn("Security violation: {}", e.getMessage());
    return ResponseEntity.status(HttpStatus.FORBIDDEN)
        .body(new ErrorResponse("SECURITY_VIOLATION", "Access denied"));
  }

  @ExceptionHandler(Exception.class)
  public ResponseEntity<ErrorResponse> handleGeneral(Exception e) {
    log.error("Unexpected error occurred", e);
    return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
        .body(new ErrorResponse("INTERNAL_ERROR", "An unexpected error occurred"));
  }
}
