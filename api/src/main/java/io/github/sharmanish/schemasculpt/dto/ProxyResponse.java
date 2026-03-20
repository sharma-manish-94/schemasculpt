package io.github.sharmanish.schemasculpt.dto;

import java.util.Map;

public record ProxyResponse(int statusCode, Map<String, String> headers, Object body) {}
