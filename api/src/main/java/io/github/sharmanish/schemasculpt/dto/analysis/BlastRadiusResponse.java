package io.github.sharmanish.schemasculpt.dto.analysis;

import java.util.List;
import lombok.Builder;
import lombok.Data;

@Data
@Builder
public class BlastRadiusResponse {
  private String targetSchema;
  private int totalEndpoints;
  private int affectedCount;
  private double impactPercentage;
  private String riskLevel; // LOW, MEDIUM, CRITICAL
  private List<String> affectedPaths;
}
