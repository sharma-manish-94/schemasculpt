package io.github.sharmanish.schemasculpt.dto.analysis;

/**
 * A record to hold code quality metrics for a symbol.
 *
 * @param complexity The cyclomatic or cognitive complexity score.
 */
public record CodeMetrics(double complexity) {}
