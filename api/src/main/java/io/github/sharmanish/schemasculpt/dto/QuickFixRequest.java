package io.github.sharmanish.schemasculpt.dto;

import java.util.Map;

public record QuickFixRequest(
    String specText, String ruleId, Map<String, Object> context, String format) {}
