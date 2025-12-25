package io.github.sharmanish.schemasculpt.dto.repository;

import com.fasterxml.jackson.annotation.JsonAlias;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/** Information about a file or directory in a repository */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class FileInfo {

  private String path;
  private String name;
  private String type; // "file" or "dir"
  private Long size;
  private String sha;
  private String url;

  @JsonProperty("is_openapi_spec")
  @JsonAlias({"isOpenApiSpec", "is_openapi_spec"})
  private boolean isOpenApiSpec;
}
