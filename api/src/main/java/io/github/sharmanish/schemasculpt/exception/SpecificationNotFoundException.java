package io.github.sharmanish.schemasculpt.exception;

/**
 * Exception thrown when a specification version cannot be found. Maps to HTTP 404 Not Found.
 */
public final class SpecificationNotFoundException extends ResourceNotFoundException {

  public SpecificationNotFoundException(String version) {
    super(ErrorCode.SPECIFICATION_NOT_FOUND, "Specification version '" + version + "' not found");
  }
}
