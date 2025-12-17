package io.github.sharmanish.schemasculpt.dto.request;

public record UpdateOperationRequest(
    String path, String method, String summary, String description) {
}
