package io.github.sharmanish.schemasculpt.dto.repository;

import com.fasterxml.jackson.annotation.JsonAlias;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/** Request to connect to a repository provider (GitHub, GitLab, etc.) */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class RepositoryConnectionRequest {

  /** Repository provider name (github, gitlab) */
  private String provider;

  /**
   * OAuth access token for authentication Accepts both camelCase (from UI) and snake_case (from AI
   * service) Serializes as snake_case for AI service compatibility
   */
  @JsonProperty("access_token")
  @JsonAlias({"accessToken", "access_token"})
  private String accessToken;
}
