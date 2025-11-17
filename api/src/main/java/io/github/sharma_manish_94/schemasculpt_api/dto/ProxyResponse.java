package io.github.sharma_manish_94.schemasculpt_api.dto;

import java.util.Map;

public record ProxyResponse(int statusCode, Map<String, String> headers, Object body) {}
