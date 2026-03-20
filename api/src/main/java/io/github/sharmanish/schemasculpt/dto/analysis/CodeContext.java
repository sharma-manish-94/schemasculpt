package io.github.sharmanish.schemasculpt.dto.analysis;

import java.util.List;

/**
 * A record to hold contextual information about a piece of source code retrieved from RepoMind.
 *
 * @param filePath The path to the source file.
 * @param codeSnippet The actual source code of the implementing function/method.
 * @param complexityScore The calculated cyclomatic or cognitive complexity.
 * @param testCoverage A simple measure of test coverage, like number of test cases.
 * @param authors A list of primary authors or contributors to the file.
 */
public record CodeContext(
    String filePath,
    String codeSnippet,
    double complexityScore,
    int testCoverage,
    List<String> authors) {}
