package io.github.sharma_manish_94.schemasculpt_api.dto.ai;

import com.fasterxml.jackson.annotation.JsonValue;

public enum StreamingMode {
    DISABLED("disabled"),
    ENABLED("enabled"),
    CHUNKS_ONLY("chunks_only"),
    FULL_RESPONSE("full_response");

    private final String value;

    StreamingMode(String value) {
        this.value = value;
    }

    @JsonValue
    public String getValue() {
        return value;
    }

    public static StreamingMode fromValue(String value) {
        for (StreamingMode mode : values()) {
            if (mode.value.equals(value)) {
                return mode;
            }
        }
        throw new IllegalArgumentException("Unknown streaming mode: " + value);
    }
}