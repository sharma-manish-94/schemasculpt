package io.github.sharma_manish_94.schemasculpt_api.dto;

import java.util.Map;

public record QuickFixRequest(
    String specText, String ruleId, Map<String, Object> context, String format) {
}
