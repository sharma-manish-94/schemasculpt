package io.github.sharmanish.schemasculpt.dto.repository;

/**
 * Response with file content from repository.
 *
 * @param path Full path to the file
 * @param content File content (decoded if was base64)
 * @param encoding Content encoding (typically "base64" or "utf-8")
 * @param size File size in bytes
 * @param sha Git SHA of the file
 * @param url API URL for the file
 */
public record ReadFileResponse(
    String path, String content, String encoding, int size, String sha, String url) {}
