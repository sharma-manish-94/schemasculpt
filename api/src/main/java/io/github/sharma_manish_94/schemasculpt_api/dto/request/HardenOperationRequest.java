package io.github.sharma_manish_94.schemasculpt_api.dto.request;

import com.fasterxml.jackson.annotation.JsonInclude;
import java.util.List;

@JsonInclude(JsonInclude.Include.NON_EMPTY)
public record HardenOperationRequest(
    String path, String method, List<String> patterns, HardeningOptions options) {
  public record HardeningOptions(
      boolean addOAuth2,
      boolean addRateLimiting,
      boolean addCaching,
      boolean addIdempotency,
      boolean addValidation,
      boolean addErrorHandling,
      String rateLimitPolicy,
      String cacheTTL,
      String securityScheme) {
  }
}
