package io.github.sharmanish.schemasculpt.dto.analysis;

/**
 * A record representing a security finding that has been enriched with context from the source code
 * implementation.
 *
 * @param originalFindingId The ID of the original finding from the spec analysis.
 * @param message The human-readable description of the finding.
 * @param severity The severity level (e.g., "CRITICAL", "HIGH").
 * @param isConfirmed True if code analysis confirms the vulnerability is present.
 * @param confirmationDetail A detailed explanation of why the vulnerability is confirmed or denied,
 *     based on code.
 * @param codeContext The context of the source code related to this finding.
 */
public record EnrichedSecurityFinding(
    String originalFindingId,
    String message,
    String severity,
    boolean isConfirmed,
    String confirmationDetail,
    CodeContext codeContext) {}
