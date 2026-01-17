package io.github.sharmanish.schemasculpt.dto.repository;

import com.fasterxml.jackson.annotation.JsonAlias;
import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.constraints.NotBlank;

/**
 * Request to connect to a repository provider (GitHub, GitLab, etc.).
 *
 * @param provider    Repository provider name (github, gitlab)
 * @param accessToken OAuth access token for authentication
 */
public record RepositoryConnectionRequest(
    @NotBlank(message = "Provider must not be blank") String provider,
    @JsonProperty("access_token")
    @JsonAlias({"accessToken", "access_token"})
    @NotBlank(message = "Access token must not be blank")
    String accessToken) {}
