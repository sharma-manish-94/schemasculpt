package io.github.sharmanish.schemasculpt.dto.repository;

import java.util.List;

/**
 * Response with repository tree contents.
 *
 * @param files  List of files and directories at the specified path
 * @param path   Current path in the repository
 * @param branch Current branch being viewed
 */
public record BrowseTreeResponse(List<FileInfo> files, String path, String branch) {

  /**
   * Creates a BrowseTreeResponse with an immutable copy of the files list.
   */
  public BrowseTreeResponse {
    files = files != null ? List.copyOf(files) : List.of();
  }
}
