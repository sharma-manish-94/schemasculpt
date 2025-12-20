package io.github.sharmanish.schemasculpt.dto.diff;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class DiffEntry {
  private String id; // E.g., "GET /users -> responses.200 -> id"
  private ChangeType type; // BREAKING, DANGEROUS, SAFE, INFO
  private String category; // OPERATION_REMOVED, TYPE_CHANGED, etc.
  private String message;
  private String oldValue;
  private String newValue;

  public enum ChangeType {
    BREAKING,   // Will definitely break clients (e.g., removing required field)
    DANGEROUS,  // Might break clients (e.g., loosening validation)
    SAFE,       // Backward compatible (e.g., adding optional field)
    INFO        // Documentation updates
  }
}
