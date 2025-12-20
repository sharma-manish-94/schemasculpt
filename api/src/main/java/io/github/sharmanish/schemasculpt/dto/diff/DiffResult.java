package io.github.sharmanish.schemasculpt.dto.diff;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class DiffResult {
  private List<DiffEntry> changes;
  private int breakingCount;
  private int dangerousCount;
  private int safeCount;
  private double structuralDriftScore;
  private String evolutionSummary;
}
