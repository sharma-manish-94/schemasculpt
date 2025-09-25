package io.github.sharma_manish_94.schemasculpt_api.dto.ai;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.time.Instant;
import java.util.List;
import java.util.Map;

public record EnhancedAIResponse(
    @JsonProperty("updated_spec_text") String updatedSpecText,
    @JsonProperty("operation_type") OperationType operationType,
    @JsonProperty("success") Boolean success,
    @JsonProperty("error_message") String errorMessage,
    @JsonProperty("processing_time_ms") Long processingTimeMs,
    @JsonProperty("model_used") String modelUsed,
    @JsonProperty("session_id") String sessionId,
    @JsonProperty("suggestions") List<String> suggestions,
    @JsonProperty("validation_errors") List<Map<String, Object>> validationErrors,
    @JsonProperty("metadata") Map<String, Object> metadata,
    @JsonProperty("created_at") Instant createdAt,
    @JsonProperty("streaming_complete") Boolean streamingComplete
) {
    // Constructor for backward compatibility
    public EnhancedAIResponse(String updatedSpecText) {
        this(updatedSpecText, OperationType.MODIFY, true, null, null, null,
             null, null, null, null, Instant.now(), false);
    }

    // Constructor for error responses
    public static EnhancedAIResponse error(String errorMessage, OperationType operationType) {
        return new EnhancedAIResponse(null, operationType, false, errorMessage, null,
                                    null, null, null, null, null, Instant.now(), false);
    }
}