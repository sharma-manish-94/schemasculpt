package io.github.sharmanish.schemasculpt.dto.repository;

import java.util.List;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * Response with repository tree contents
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class BrowseTreeResponse {

  private List<FileInfo> files;
  private String path;
  private String branch;
}
