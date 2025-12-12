package io.github.sharma_manish_94.schemasculpt_api.dto.repository;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

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
