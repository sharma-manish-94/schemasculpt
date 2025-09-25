package io.github.sharma_manish_94.schemasculpt_api.dto.ai;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;
import java.util.Map;

public record GenerateSpecRequest(
    String domain,
    String description,
    @JsonProperty("api_type") String apiType,
    @JsonProperty("complexity_level") String complexityLevel,
    @JsonProperty("include_examples") Boolean includeExamples,
    @JsonProperty("authentication_type") String authenticationType,
    @JsonProperty("additional_requirements") List<String> additionalRequirements,
    @JsonProperty("streaming") StreamingMode streaming,
    @JsonProperty("user_id") String userId,
    @JsonProperty("session_id") String sessionId,
    @JsonProperty("custom_schemas") Map<String, Object> customSchemas,
    @JsonProperty("target_version") String targetVersion
) {
    public GenerateSpecRequest {
        if (streaming == null) {
            streaming = StreamingMode.DISABLED;
        }
        if (complexityLevel == null) {
            complexityLevel = "medium";
        }
        if (includeExamples == null) {
            includeExamples = true;
        }
        if (targetVersion == null) {
            targetVersion = "3.0.3";
        }
    }

    // Simple constructor for basic generation
    public GenerateSpecRequest(String domain, String description) {
        this(domain, description, "REST", "medium", true, null, null,
             StreamingMode.DISABLED, null, null, null, "3.0.3");
    }
}