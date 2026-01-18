package io.github.sharmanish.schemasculpt.dto.repository;

import com.fasterxml.jackson.annotation.JsonAlias;
import com.fasterxml.jackson.annotation.JsonProperty;
import java.time.LocalDateTime;

/**
 * Information about a repository.
 *
 * @param owner         Repository owner (user or organization)
 * @param name          Repository name
 * @param fullName      Full repository name (owner/repo)
 * @param description   Repository description
 * @param url           Repository URL
 * @param defaultBranch Default branch name
 * @param isPrivate     Whether the repository is private
 * @param createdAt     Repository creation timestamp
 * @param updatedAt     Last update timestamp
 */
public record RepositoryInfo(
    String owner,
    String name,
    @JsonProperty("full_name")
    @JsonAlias({"fullName", "full_name"})
    String fullName,
    String description,
    String url,
    @JsonProperty("default_branch")
    @JsonAlias({"defaultBranch", "default_branch"})
    String defaultBranch,
    @JsonProperty("private")
    @JsonAlias({"isPrivate", "private"})
    boolean isPrivate,
    @JsonProperty("created_at")
    @JsonAlias({"createdAt", "created_at"})
    LocalDateTime createdAt,
    @JsonProperty("updated_at")
    @JsonAlias({"updatedAt", "updated_at"})
    LocalDateTime updatedAt) {}
