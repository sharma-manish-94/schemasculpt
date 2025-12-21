package io.github.sharmanish.schemasculpt.service.analyzer.base;

import io.github.sharmanish.schemasculpt.service.analyzer.Analyzer;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.media.Schema;
import lombok.extern.slf4j.Slf4j;

import java.util.Collections;
import java.util.Map;
import java.util.Optional;
import java.util.Set;

/**
 * Abstract base class for OpenAPI analyzers providing common utilities.
 *
 * <p>Implements template method pattern with final {@code analyze()} method
 * that performs validation before delegating to {@code performAnalysis()}.
 *
 * @param <T> The type of analysis result
 */
@Slf4j
public abstract class AbstractSchemaAnalyzer<T> implements Analyzer<T> {

  protected static final String COMPONENTS_SCHEMAS_PREFIX = "#/components/schemas/";
  protected static final String OPERATION_PREFIX = "Operations: ";
  protected static final String SCHEMA_PREFIX = "Schema: ";
  protected static final Set<String> SENSITIVE_KEYWORDS =
      Set.of(
          "password",
          "secret",
          "token",
          "key",
          "ssn",
          "socialsecurity",
          "creditcard",
          "cardnumber",
          "cvv",
          "pii",
          "salary",
          "internal");

  /**
   * Template method that validates input and delegates to performAnalysis.
   *
   * @param openApi The OpenAPI specification
   * @return Analysis result
   */
  @Override
  public final T analyze(OpenAPI openApi) {
    log.debug("Starting analysis: {}", getName());
    validateOpenApi(openApi);
    return performAnalysis(openApi);
  }

  /**
   * Performs the actual analysis implementation.
   *
   * @param openApi The validated OpenAPI specification
   * @return Analysis result
   */
  protected abstract T performAnalysis(OpenAPI openApi);

  /**
   * Validates the OpenAPI specification.
   *
   * @param openApi The OpenAPI specification
   * @throws IllegalArgumentException if spec is null
   */
  protected void validateOpenApi(OpenAPI openApi) {
    if (openApi == null) {
      throw new IllegalArgumentException("OpenAPI specification cannot be null");
    }
  }

  /**
   * Gets all schemas from components section.
   *
   * @param openApi The OpenAPI specification
   * @return Map of schema name to schema object, or empty map if none
   */
  protected Map<String, Schema> getAllSchemas(OpenAPI openApi) {
    return Optional.ofNullable(openApi.getComponents())
        .map(c -> c.getSchemas())
        .orElse(Collections.emptyMap());
  }

  /**
   * Extracts schema name from a $ref path.
   *
   * @param refPath The $ref path (e.g., "#/components/schemas/User")
   * @return The schema name (e.g., "User"), or null if invalid
   */
  protected String extractSchemaName(String refPath) {
    if (refPath == null || !refPath.startsWith(COMPONENTS_SCHEMAS_PREFIX)) {
      return null;
    }
    return refPath.substring(COMPONENTS_SCHEMAS_PREFIX.length());
  }
}
