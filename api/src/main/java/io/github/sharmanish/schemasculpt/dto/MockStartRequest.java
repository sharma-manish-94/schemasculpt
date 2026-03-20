package io.github.sharmanish.schemasculpt.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

public record MockStartRequest(@JsonProperty("spec_text") String specText) {}
