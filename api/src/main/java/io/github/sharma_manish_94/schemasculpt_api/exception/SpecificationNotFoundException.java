package io.github.sharma_manish_94.schemasculpt_api.exception;

public class SpecificationNotFoundException extends SchemaSculptException {

  public SpecificationNotFoundException(String version) {
    super("SPECIFICATION_NOT_FOUND", "Specification version '" + version + "' not found");
  }
}
