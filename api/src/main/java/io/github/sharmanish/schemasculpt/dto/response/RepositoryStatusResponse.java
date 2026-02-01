package io.github.sharmanish.schemasculpt.dto.response;

public record RepositoryStatusResponse(
    String path,
    String status, // e.g., "INDEXING", "INDEXED", "NOT_FOUND", "ERROR"
    int indexedFileCount,
    String lastIndexed) {}
