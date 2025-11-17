package io.github.sharma_manish_94.schemasculpt_api.dto.repository;

import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;
import java.time.LocalDateTime;

/**
 * Information about a repository
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class RepositoryInfo {

    private String owner;
    private String name;
    private String fullName;
    private String description;
    private String url;
    private String defaultBranch;
    private boolean isPrivate;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}
