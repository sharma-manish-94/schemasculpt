package io.github.sharma_manish_94.schemasculpt_api.dto.repository;

import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;
import java.util.List;

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
