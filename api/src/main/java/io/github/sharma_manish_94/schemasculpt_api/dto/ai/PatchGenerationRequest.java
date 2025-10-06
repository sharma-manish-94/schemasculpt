package io.github.sharma_manish_94.schemasculpt_api.dto.ai;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.Map;

/** Request to AI service for generating JSON Patch operations. */
public record PatchGenerationRequest(
    @JsonProperty("spec_text") String specText,
    @JsonProperty("rule_id") String ruleId,
    @JsonProperty("context") Map<String, Object> context,
    @JsonProperty("suggestion_message") String suggestionMessage) {}
