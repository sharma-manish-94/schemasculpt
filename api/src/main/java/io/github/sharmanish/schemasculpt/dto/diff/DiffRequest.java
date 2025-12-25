package io.github.sharmanish.schemasculpt.dto.diff;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class DiffRequest {
  /** The original (baseline) OpenAPI specification content (JSON or YAML string). */
  private String oldSpec;

  /** The new (proposed) OpenAPI specification content (JSON or YAML string). */
  private String newSpec;
}
