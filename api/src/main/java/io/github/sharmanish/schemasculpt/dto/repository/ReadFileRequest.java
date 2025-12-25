package io.github.sharmanish.schemasculpt.dto.repository;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/** Request to read a file from repository */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class ReadFileRequest {

  private String owner;
  private String repo;
  private String path;
  private String ref; // Optional: branch, tag, or commit SHA
}
