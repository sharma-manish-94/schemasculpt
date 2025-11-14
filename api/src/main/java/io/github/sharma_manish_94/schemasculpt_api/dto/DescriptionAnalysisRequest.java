package io.github.sharma_manish_94.schemasculpt_api.dto;

import java.util.List;

/**
 * Request DTO for AI-powered description quality analysis. Sends only necessary context to AI (not
 * entire spec).
 */
public record DescriptionAnalysisRequest(List<DescriptionItem> items) {
  public record DescriptionItem(
      String path, // e.g., "/paths/~1users~1{id}/get" or "/components/schemas/User"
      String type, // "operation", "schema", "parameter", "response"
      String currentDescription, // May be null or empty
      DescriptionContext context) {}

  public record DescriptionContext(
      String method, // For operations: GET, POST, etc.
      String schemaType, // For schemas: object, array, etc.
      List<String> propertyNames, // For schemas: list of property names for context
      String operationSummary, // For operations: existing summary for context
      Integer statusCode // For responses: 200, 404, etc.
      ) {}
}
