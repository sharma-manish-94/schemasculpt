package io.github.sharmanish.schemasculpt.dto.repository;

/**
 * Response after connecting to a repository provider.
 *
 * @param success  Whether the connection was successful
 * @param message  Status message or error description
 * @param provider The repository provider that was connected to
 */
public record RepositoryConnectionResponse(boolean success, String message, String provider) {}
