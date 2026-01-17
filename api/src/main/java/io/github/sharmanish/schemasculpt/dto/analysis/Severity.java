package io.github.sharmanish.schemasculpt.dto.analysis;

import com.fasterxml.jackson.annotation.JsonValue;

/**
 * Sealed hierarchy for security vulnerability severity levels.
 * Provides type-safe severity classification with JSON serialization support.
 *
 * <p>Per Effective Java Item 23: Prefer class hierarchies to tagged classes.
 * Using sealed types instead of String provides compile-time safety.
 */
public sealed interface Severity permits Severity.Critical, Severity.Warning, Severity.Info {

  /**
   * Returns the severity level name for JSON serialization.
   */
  @JsonValue
  String name();

  /**
   * Critical severity: Immediate security risk requiring urgent attention.
   * Examples: Public endpoint exposing PII, unprotected sensitive data.
   */
  record Critical() implements Severity {
    @Override
    public String name() {
      return "CRITICAL";
    }
  }

  /**
   * Warning severity: Potential security concern requiring review.
   * Examples: Secured endpoint returning sensitive data, verify necessity.
   */
  record Warning() implements Severity {
    @Override
    public String name() {
      return "WARNING";
    }
  }

  /**
   * Info severity: Informational finding, low risk.
   * Examples: Best practice suggestions, minor improvements.
   */
  record Info() implements Severity {
    @Override
    public String name() {
      return "INFO";
    }
  }

  // Singleton instances for common use
  Severity CRITICAL = new Critical();
  Severity WARNING = new Warning();
  Severity INFO = new Info();
}
