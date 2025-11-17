package io.github.sharma_manish_94.schemasculpt_api.dto.repository;

import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;

/**
 * Response with file content from repository
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class ReadFileResponse {

    private String path;
    private String content;
    private String encoding;
    private int size;
    private String sha;
    private String url;
}
