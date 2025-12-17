package io.github.sharmanish.schemasculpt.dto.ai;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;

/**
 * Response from AI service containing JSON Patch operations.
 */
public record PatchGenerationResponse(
    @JsonProperty("patches") List<JsonPatchOperation> patches,
    @JsonProperty("explanation") String explanation,
    @JsonProperty("rule_id") String ruleId,
    @JsonProperty("confidence") Double confidence,
    @JsonProperty("warnings") List<String> warnings) {
}
