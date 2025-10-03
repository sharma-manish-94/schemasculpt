package io.github.sharma_manish_94.schemasculpt_api.dto;

import com.fasterxml.jackson.annotation.JsonInclude;
import java.util.List;
import java.util.Map;

@JsonInclude(JsonInclude.Include.NON_EMPTY)
public record ExplanationResponse(
        String explanation,
        String severity,
        String category,
        List<String> relatedBestPractices,
        List<String> exampleSolutions,
        List<String> additionalResources,
        Map<String, Object> metadata
) {
    public ExplanationResponse(String explanation) {
        this(explanation, "info", "general", List.of(), List.of(), List.of(), Map.of());
    }

    public ExplanationResponse(String explanation, String severity, String category) {
        this(explanation, severity, category, List.of(), List.of(), List.of(), Map.of());
    }
}