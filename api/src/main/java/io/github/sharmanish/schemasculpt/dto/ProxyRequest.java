package io.github.sharmanish.schemasculpt.dto;

import java.util.Map;

public record ProxyRequest(String method, String url, Map<String, String> headers, String body) {}
