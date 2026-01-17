package io.github.sharmanish.schemasculpt.dto.diff;

/**
 * Represents a single change between two OpenAPI specifications.
 *
 * @param id       Unique identifier for the change (e.g., "GET /users -> responses.200 -> id")
 * @param type     Classification of the change impact
 * @param category Type of change (e.g., OPERATION_REMOVED, TYPE_CHANGED)
 * @param message  Human-readable description of the change
 * @param oldValue The original value before the change
 * @param newValue The new value after the change
 */
public record DiffEntry(
    String id,
    ChangeType type,
    String category,
    String message,
    String oldValue,
    String newValue) {

  /**
   * Classification of API change impact on clients.
   */
  public enum ChangeType {
    /** Will definitely break clients (e.g., removing required field) */
    BREAKING,
    /** Might break clients (e.g., loosening validation) */
    DANGEROUS,
    /** Backward compatible (e.g., adding optional field) */
    SAFE,
    /** Documentation updates */
    INFO
  }
}
