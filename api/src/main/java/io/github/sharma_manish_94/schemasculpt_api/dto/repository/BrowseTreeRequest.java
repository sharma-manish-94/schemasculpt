package io.github.sharma_manish_94.schemasculpt_api.dto.repository;

import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;

/**
 * Request to browse repository tree
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class BrowseTreeRequest {

    private String owner;
    private String repo;
    private String path = "";  // Default to root
    private String branch;      // Optional branch name
}
