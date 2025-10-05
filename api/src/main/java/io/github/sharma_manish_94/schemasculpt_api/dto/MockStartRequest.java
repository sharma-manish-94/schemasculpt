package io.github.sharma_manish_94.schemasculpt_api.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

public record MockStartRequest(@JsonProperty("spec_text") String specText) {}
