package io.github.sharma_manish_94.schemasculpt_api.dto.analysis;

import com.fasterxml.jackson.annotation.JsonInclude;
import java.util.List;
import java.util.Map;

/**
 * Represents a single factual security finding extracted by deterministic Java analysis.
 * These findings are sent to the AI for reasoning about attack chains.
 */
@JsonInclude(JsonInclude.Include.NON_NULL)
public record SecurityFinding(
    String type,
    // Type of finding: "PUBLIC_ENDPOINT", "SCHEMA_FIELD", "ENDPOINT_ACCEPTS_SCHEMA", etc.
    String severity, // "CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"
    String category, // "security", "data-exposure", "mass-assignment", etc.
    String endpoint, // e.g., "GET /users/all"
    String description, // Human-readable description
    Map<String, Object> metadata
    // Additional context (schema names, field names, dependencies, etc.)
) {

  /**
   * Factory method for public endpoint findings
   */
  public static SecurityFinding publicEndpoint(String method, String path) {
    return new SecurityFinding(
        "PUBLIC_ENDPOINT",
        "HIGH",
        "security",
        method + " " + path,
        String.format("Endpoint %s %s has no security requirements (publicly accessible)", method,
            path),
        Map.of("method", method, "path", path)
    );
  }

  /**
   * Factory method for endpoint returning a schema
   */
  public static SecurityFinding endpointReturnsSchema(String method, String path, String schemaName,
                                                      List<String> fields) {
    return new SecurityFinding(
        "ENDPOINT_RETURNS_SCHEMA",
        "INFO",
        "data-exposure",
        method + " " + path,
        String.format("Endpoint %s %s returns schema '%s'", method, path, schemaName),
        Map.of(
            "method", method,
            "path", path,
            "schema", schemaName,
            "fields", fields
        )
    );
  }

  /**
   * Factory method for endpoint accepting a schema
   */
  public static SecurityFinding endpointAcceptsSchema(String method, String path, String schemaName,
                                                      List<String> fields) {
    return new SecurityFinding(
        "ENDPOINT_ACCEPTS_SCHEMA",
        "INFO",
        "mass-assignment",
        method + " " + path,
        String.format("Endpoint %s %s accepts schema '%s' in request body", method, path,
            schemaName),
        Map.of(
            "method", method,
            "path", path,
            "schema", schemaName,
            "fields", fields
        )
    );
  }

  /**
   * Factory method for sensitive field findings
   */
  public static SecurityFinding schemaContainsSensitiveField(String schemaName, String fieldName,
                                                             String fieldType) {
    return new SecurityFinding(
        "SENSITIVE_FIELD",
        "MEDIUM",
        "data-exposure",
        null,
        String.format("Schema '%s' contains sensitive field '%s' (type: %s)", schemaName, fieldName,
            fieldType),
        Map.of(
            "schema", schemaName,
            "field", fieldName,
            "fieldType", fieldType
        )
    );
  }

  /**
   * Factory method for writable sensitive field findings
   */
  public static SecurityFinding writableSensitiveField(String method, String path,
                                                       String schemaName, String fieldName) {
    return new SecurityFinding(
        "WRITABLE_SENSITIVE_FIELD",
        "HIGH",
        "mass-assignment",
        method + " " + path,
        String.format("Endpoint %s %s allows writing to sensitive field '%s' in schema '%s'",
            method, path, fieldName, schemaName),
        Map.of(
            "method", method,
            "path", path,
            "schema", schemaName,
            "field", fieldName
        )
    );
  }

  /**
   * Factory method for dependency chain findings
   */
  public static SecurityFinding schemaDependency(String sourceSchema, String targetSchema,
                                                 String viaEndpoint) {
    return new SecurityFinding(
        "SCHEMA_DEPENDENCY",
        "INFO",
        "data-flow",
        viaEndpoint,
        String.format("Schema '%s' references schema '%s'", sourceSchema, targetSchema),
        Map.of(
            "sourceSchema", sourceSchema,
            "targetSchema", targetSchema,
            "endpoint", viaEndpoint
        )
    );
  }
}
