package io.github.sharmanish.schemasculpt.util;

@SuppressWarnings({"checkstyle:SummaryJavadoc", "checkstyle:MissingJavadocType"})
public class LogSanitizer {
  private LogSanitizer() {}

  /**
   * Replaces newline characters with underscores to prevent Log Injection attacks.
   *
   * @param content The raw string to log
   * @return A sanitized string safe for logging
   */
  public static String sanitize(Object content) {
    if (content == null) {
      return "null";
    }
    return content.toString().replaceAll("[\r\n]", "_");
  }
}
