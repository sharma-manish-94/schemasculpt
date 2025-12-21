package io.github.sharmanish.schemasculpt.service.analyzer;

import io.swagger.v3.oas.models.OpenAPI;

/**
 * Generic interface for OpenAPI specification analyzers.
 * Follows the Strategy pattern with type-safe return values.
 *
 * <p>Each analyzer implements a specific analysis algorithm (e.g., dependency graph,
 * taint analysis, schema similarity) and returns a strongly-typed result.
 *
 * @param <T> The type of analysis result
 */
public interface Analyzer<T> {

  /**
   * Performs analysis on the OpenAPI specification.
   *
   * @param openApi The parsed OpenAPI specification
   * @return Type-safe analysis result
   */
  T analyze(OpenAPI openApi);

  /**
   * Returns the analyzer name for logging and identification purposes.
   *
   * @return The simple class name of the analyzer
   */
  default String getName() {
    return this.getClass().getSimpleName();
  }
}
