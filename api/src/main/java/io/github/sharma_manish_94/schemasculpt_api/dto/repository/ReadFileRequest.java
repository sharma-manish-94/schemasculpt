package io.github.sharma_manish_94.schemasculpt_api.dto.repository;

import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;

/**
 * Request to read a file from repository
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class ReadFileRequest {

    private String owner;
    private String repo;
    private String path;
    private String ref;  // Optional: branch, tag, or commit SHA
}
