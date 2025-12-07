package io.github.sharma_manish_94.schemasculpt_api.dto.analysis;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;

/**
 * Request payload for the Linter-Augmented AI Analyst.
 * Instead of sending the entire 5MB spec, we send only the factual findings
 * extracted by deterministic Java analysis. The AI then reasons about attack chains.
 */
public record SecurityFindingsRequest(
        @JsonProperty("findings") List<SecurityFinding> findings,
        @JsonProperty("analysis_depth") String analysisDepth,
        @JsonProperty("max_chain_length") int maxChainLength,
        @JsonProperty("exclude_low_severity") boolean excludeLowSeverity
) {
    public SecurityFindingsRequest(List<SecurityFinding> findings) {
        this(findings, "standard", 5, false);
    }

    public SecurityFindingsRequest(List<SecurityFinding> findings, String analysisDepth) {
        this(findings, analysisDepth, 5, false);
    }
}
