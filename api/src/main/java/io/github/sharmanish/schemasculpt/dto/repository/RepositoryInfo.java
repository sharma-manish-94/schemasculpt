package io.github.sharmanish.schemasculpt.dto.repository;

import com.fasterxml.jackson.annotation.JsonAlias;
import com.fasterxml.jackson.annotation.JsonProperty;
import java.time.LocalDateTime;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * Information about a repository
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class RepositoryInfo {

  private String owner;
  private String name;

  @JsonProperty("full_name")
  @JsonAlias({"fullName", "full_name"})
  private String fullName;

  private String description;
  private String url;

  @JsonProperty("default_branch")
  @JsonAlias({"defaultBranch", "default_branch"})
  private String defaultBranch;

  @JsonProperty("private")
  @JsonAlias({"isPrivate", "private"})
  private boolean isPrivate;

  @JsonProperty("created_at")
  @JsonAlias({"createdAt", "created_at"})
  private LocalDateTime createdAt;

  @JsonProperty("updated_at")
  @JsonAlias({"updatedAt", "updated_at"})
  private LocalDateTime updatedAt;
}
