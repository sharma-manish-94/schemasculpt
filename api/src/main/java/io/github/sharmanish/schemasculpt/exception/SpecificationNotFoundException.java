package io.github.sharmanish.schemasculpt.exception;

public class SpecificationNotFoundException extends SchemaSculptException {

  public SpecificationNotFoundException(String version) {
    super("SPECIFICATION_NOT_FOUND", "Specification version '" + version + "' not found");
  }
}
