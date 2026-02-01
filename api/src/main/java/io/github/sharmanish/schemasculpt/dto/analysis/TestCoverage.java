package io.github.sharmanish.schemasculpt.dto.analysis;

/**
 * A record to hold test coverage information for a symbol.
 *
 * @param testFileCount The number of test files found.
 * @param testCaseCount The number of individual test cases found.
 */
public record TestCoverage(int testFileCount, int testCaseCount) {}
