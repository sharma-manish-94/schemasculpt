package io.github.sharma_manish_94.schemasculpt_api.dto.ai;

import com.fasterxml.jackson.annotation.JsonValue;

public enum OperationType {
    MODIFY("modify"),
    GENERATE("generate"),
    VALIDATE("validate"),
    OPTIMIZE("optimize"),
    DOCUMENT("document"),
    MOCK("mock"),
    ANALYZE("analyze");

    private final String value;

    OperationType(String value) {
        this.value = value;
    }

    @JsonValue
    public String getValue() {
        return value;
    }

    public static OperationType fromValue(String value) {
        for (OperationType type : values()) {
            if (type.value.equals(value)) {
                return type;
            }
        }
        throw new IllegalArgumentException("Unknown operation type: " + value);
    }
}