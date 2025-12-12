package io.github.sharma_manish_94.schemasculpt_api.dto;

import java.util.Map;

public record ProxyRequest(String method, String url, Map<String, String> headers, String body) {
}
