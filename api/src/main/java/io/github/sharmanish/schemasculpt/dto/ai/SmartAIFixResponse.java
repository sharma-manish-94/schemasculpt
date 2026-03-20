package io.github.sharmanish.schemasculpt.dto.ai;

import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;

/**
 * Response from smart AI fix endpoint. Handles both camelCase (Java) and snake_case (Python) field
 * names.
 */
@JsonInclude(JsonInclude.Include.NON_NULL)
public record SmartAIFixResponse(
    @JsonProperty("updated_spec_text") String updatedSpecText,
    @JsonProperty("method_used") String methodUsed, // "patch" or "full_regeneration"
    @JsonProperty("patches_applied") List<JsonPatchOperation> patchesApplied,
    String explanation,
    Double confidence,
    @JsonProperty("processing_time_ms") Double processingTimeMs,
    @JsonProperty("token_count") Integer tokenCount,
    List<String> warnings) {}
