package io.github.sharma_manish_94.schemasculpt_api.dto.ai;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.time.Instant;
import java.util.List;
import java.util.Map;

/**
 * Raw response structure from AI service - matches the actual AI service response format
 */
public record AIServiceResponse(
    @JsonProperty("updated_spec_text") String updatedSpecText,
    @JsonProperty("operation_type") String operationType,
    Map<String, Object> validation,
    @JsonProperty("confidence_score") Double confidenceScore,
    @JsonProperty("changes_summary") String changesSummary,
    @JsonProperty("applied_patches") List<Map<String, Object>> appliedPatches,
    @JsonProperty("modified_paths") List<String> modifiedPaths,
    @JsonProperty("request_id") String requestId,
    String timestamp,
    Map<String, Object> performance,
    Map<String, Object> context,
    @JsonProperty("follow_up_suggestions") List<String> followUpSuggestions
) {
    /**
     * Convert AI service response to our enhanced response format
     */
    public EnhancedAIResponse toEnhancedResponse() {
        // Extract performance data
        Long processingTime = null;
        String modelUsed = null;
        if (performance != null) {
            Object timeObj = performance.get("processing_time_ms");
            if (timeObj instanceof Number) {
                processingTime = ((Number) timeObj).longValue();
            }
            modelUsed = (String) performance.get("model_used");
        }

        // Extract validation data
        List<Map<String, Object>> validationErrors = null;
        List<String> suggestions = null;
        if (validation != null) {
            validationErrors = (List<Map<String, Object>>) validation.get("errors");

            // Convert warnings and suggestions to suggestions list
            List<String> warnings = (List<String>) validation.get("warnings");
            List<String> validationSuggestions = (List<String>) validation.get("suggestions");

            suggestions = followUpSuggestions;
            if (suggestions == null) {
                suggestions = validationSuggestions;
            }
            if (suggestions == null && warnings != null) {
                suggestions = warnings;
            }
        }

        // Extract session ID from context
        String sessionId = null;
        if (context != null) {
            sessionId = (String) context.get("conversation_id");
        }

        // Determine success based on presence of spec and lack of critical errors
        boolean success = updatedSpecText != null && !updatedSpecText.isEmpty();
        if (validationErrors != null && !validationErrors.isEmpty()) {
            // Check if there are critical errors
            success = validationErrors.stream().noneMatch(error ->
                "error".equals(error.get("severity")) || "critical".equals(error.get("severity"))
            );
        }

        // Parse operation type
        OperationType opType;
        try {
            opType = OperationType.fromValue(operationType);
        } catch (Exception e) {
            opType = OperationType.MODIFY;
        }

        // Create metadata
        Map<String, Object> metadata = Map.of(
            "confidence_score", confidenceScore != null ? confidenceScore : 0.0,
            "changes_summary", changesSummary != null ? changesSummary : "",
            "request_id", requestId != null ? requestId : ""
        );

        return new EnhancedAIResponse(
            updatedSpecText,
            opType,
            success,
            null, // No error message if successful
            processingTime,
            modelUsed,
            sessionId,
            suggestions,
            validationErrors,
            metadata,
            Instant.now(),
            false
        );
    }
}