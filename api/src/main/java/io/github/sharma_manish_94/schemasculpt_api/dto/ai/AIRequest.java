package io.github.sharma_manish_94.schemasculpt_api.dto.ai;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;
import java.util.Map;

public record AIRequest(
    @JsonProperty("spec_text") String specText,
    String prompt,
    @JsonProperty("operation_type") OperationType operationType,
    @JsonProperty("session_id") String sessionId,
    @JsonProperty("user_id") String userId,
    @JsonProperty("streaming") StreamingMode streaming,
    @JsonProperty("json_patches") List<Map<String, Object>> jsonPatches,
    Map<String, Object> context,
    @JsonProperty("response_format") String responseFormat,
    @JsonProperty("max_tokens") Integer maxTokens,
    Double temperature
) {
    public AIRequest {
        if (operationType == null) {
            operationType = OperationType.MODIFY;
        }
        if (streaming == null) {
            streaming = StreamingMode.DISABLED;
        }
    }

    // Constructor for backward compatibility
    public AIRequest(String specText, String prompt, OperationType operationType) {
        this(specText, prompt, operationType, null, null, StreamingMode.DISABLED,
             null, null, null, null, null);
    }
}