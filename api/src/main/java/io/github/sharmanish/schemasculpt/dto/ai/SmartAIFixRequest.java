package io.github.sharmanish.schemasculpt.dto.ai;

import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;

/**
 * Request for smart AI fix that intelligently chooses between patches and full regeneration. Uses
 * snake_case for Python compatibility.
 */
@JsonInclude(JsonInclude.Include.NON_NULL)
public record SmartAIFixRequest(
    @JsonProperty("specText") // Keep camelCase to match Python alias
    String specText,
    String prompt,
    @JsonProperty("target_path") String targetPath,
    @JsonProperty("target_method") String targetMethod,
    @JsonProperty("validation_errors") List<String> validationErrors,
    @JsonProperty("force_full_regeneration") Boolean forceFullRegeneration) {
  /**
   * Convenience constructor for simple requests without targeting.
   */
  public SmartAIFixRequest(String specText, String prompt) {
    this(specText, prompt, null, null, null, false);
  }

  /**
   * Convenience constructor with targeting.
   */
  public SmartAIFixRequest(String specText, String prompt, String targetPath, String targetMethod) {
    this(specText, prompt, targetPath, targetMethod, null, false);
  }
}
