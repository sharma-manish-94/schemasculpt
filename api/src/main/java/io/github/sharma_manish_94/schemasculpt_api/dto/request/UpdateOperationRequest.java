package io.github.sharma_manish_94.schemasculpt_api.dto.request;

public record UpdateOperationRequest(
        String path,
        String method,
        String summary,
        String description
) {
}
