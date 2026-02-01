package io.github.sharmanish.schemasculpt.dto.response;

public record ImplementationCodeResponse(
    String filePath, String content, int startLine, String language) {}
