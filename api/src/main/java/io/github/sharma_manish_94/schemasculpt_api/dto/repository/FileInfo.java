package io.github.sharma_manish_94.schemasculpt_api.dto.repository;

import com.fasterxml.jackson.annotation.JsonAlias;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;

/**
 * Information about a file or directory in a repository
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class FileInfo {

    private String path;
    private String name;
    private String type;  // "file" or "dir"
    private Long size;
    private String sha;
    private String url;

    @JsonProperty("is_openapi_spec")
    @JsonAlias({"isOpenApiSpec", "is_openapi_spec"})
    private boolean isOpenApiSpec;
}
