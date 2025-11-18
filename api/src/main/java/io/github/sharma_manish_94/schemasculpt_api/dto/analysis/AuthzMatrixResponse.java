package io.github.sharma_manish_94.schemasculpt_api.dto.analysis;

import java.util.List;
import java.util.Map;

public record AuthzMatrixResponse(
        List<String> scopes,            // Columns: All unique scopes found
        Map<String, List<String>> matrix // Rows: Operation ID -> List of scopes it requires
) {
}
