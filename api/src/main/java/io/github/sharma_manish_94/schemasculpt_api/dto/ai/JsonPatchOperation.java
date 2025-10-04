package io.github.sharma_manish_94.schemasculpt_api.dto.ai;

import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * Single JSON Patch operation (RFC 6902).
 */
public record JsonPatchOperation(
        @JsonProperty("op")
        String op,

        @JsonProperty("path")
        String path,

        @JsonProperty("value")
        Object value,

        @JsonProperty("from")
        String from
) {
}
