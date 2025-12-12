package io.github.sharma_manish_94.schemasculpt_api.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

public record MockSessionDetails(
    @JsonProperty("mock_id") String mockId, @JsonProperty("base_url") String baseUrl) {
}
