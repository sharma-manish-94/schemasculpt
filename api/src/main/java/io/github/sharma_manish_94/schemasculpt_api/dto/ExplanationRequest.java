package io.github.sharma_manish_94.schemasculpt_api.dto;

import com.fasterxml.jackson.annotation.JsonInclude;
import java.util.Map;

@JsonInclude(JsonInclude.Include.NON_EMPTY)
public record ExplanationRequest(
        String ruleId,
        String message,
        String specText,
        String category,
        Map<String, Object> context
) {
    public ExplanationRequest(String ruleId, String message, String specText) {
        this(ruleId, message, specText, "general", Map.of());
    }
}