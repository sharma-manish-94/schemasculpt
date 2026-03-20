package io.github.sharmanish.schemasculpt.dto.ai;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.time.Instant;
import java.util.List;

public record MockStartResponse(
    @JsonProperty("mock_id") String mockId,
    @JsonProperty("base_url") String baseUrl,
    String host,
    Integer port,
    @JsonProperty("available_endpoints") List<String> availableEndpoints,
    @JsonProperty("total_endpoints") Integer totalEndpoints,
    @JsonProperty("created_at") Instant createdAt,
    String message,
    @JsonProperty("docs_url") String docsUrl) {
  public MockStartResponse {
    if (message == null) {
      message = "Mock server started successfully";
    }
    if (createdAt == null) {
      createdAt = Instant.now();
    }
    if (docsUrl == null && baseUrl != null) {
      docsUrl = baseUrl + "/docs";
    }
  }
}
