package io.github.sharmanish.schemasculpt.dto.repository;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

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
