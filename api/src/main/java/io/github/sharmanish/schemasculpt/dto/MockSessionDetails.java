package io.github.sharmanish.schemasculpt.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

public record MockSessionDetails(
    @JsonProperty("mock_id") String mockId, @JsonProperty("base_url") String baseUrl) {}
