package io.github.sharma_manish_94.schemasculpt_api.dto.repository;

import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;

/**
 * Response after connecting to a repository provider
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class RepositoryConnectionResponse {

    private boolean success;
    private String message;
    private String provider;
}
