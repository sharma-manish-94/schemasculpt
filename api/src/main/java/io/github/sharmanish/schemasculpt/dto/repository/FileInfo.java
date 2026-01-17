package io.github.sharmanish.schemasculpt.dto.repository;

import com.fasterxml.jackson.annotation.JsonAlias;
import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * Information about a file or directory in a repository.
 *
 * @param path         Full path to the file
 * @param name         File or directory name
 * @param type         Type: "file" or "dir"
 * @param size         File size in bytes (null for directories)
 * @param sha          Git SHA of the file
 * @param url          API URL for the file
 * @param isOpenApiSpec Whether this file is detected as an OpenAPI specification
 */
public record FileInfo(
    String path,
    String name,
    String type,
    Long size,
    String sha,
    String url,
    @JsonProperty("is_openapi_spec")
    @JsonAlias({"isOpenApiSpec", "is_openapi_spec"})
    boolean isOpenApiSpec) {}
