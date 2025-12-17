package io.github.sharmanish.schemasculpt.dto.analysis;

import java.util.List;
import java.util.Map;

public record AuthzMatrixResponse(
    List<String> scopes,            // Columns: All unique scopes found
    Map<String, List<String>> matrix // Rows: Operation ID -> List of scopes it requires
) {
}
