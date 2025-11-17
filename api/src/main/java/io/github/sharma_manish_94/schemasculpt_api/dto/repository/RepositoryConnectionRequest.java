package io.github.sharma_manish_94.schemasculpt_api.dto.repository;

import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;

/**
 * Request to connect to a repository provider (GitHub, GitLab, etc.)
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class RepositoryConnectionRequest {

    /**
     * Repository provider name (github, gitlab)
     */
    private String provider;

    /**
     * OAuth access token for authentication
     */
    private String accessToken;
}
