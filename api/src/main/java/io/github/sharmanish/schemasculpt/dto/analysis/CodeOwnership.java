package io.github.sharmanish.schemasculpt.dto.analysis;

import java.util.List;

/**
 * A record to hold ownership information for a source file.
 *
 * @param authors A list of primary authors or contributors.
 */
public record CodeOwnership(List<String> authors) {}
