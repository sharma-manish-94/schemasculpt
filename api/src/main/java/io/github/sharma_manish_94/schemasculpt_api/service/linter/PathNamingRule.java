package io.github.sharma_manish_94.schemasculpt_api.service.linter;

import io.github.sharma_manish_94.schemasculpt_api.dto.ValidationSuggestion;
import io.swagger.v3.oas.models.OpenAPI;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.regex.Pattern;
import org.springframework.stereotype.Component;

/**
 * Linter rule that validates API path naming conventions following REST best practices. Ensures
 * paths use kebab-case, no trailing slashes, and proper resource naming.
 */
@Component
public class PathNamingRule implements LinterRule {

  private static final Pattern KEBAB_CASE_PATTERN = Pattern.compile("^[a-z0-9]+(-[a-z0-9]+)*$");
  private static final Pattern PATH_PARAMETER_PATTERN = Pattern.compile("\\{[^}]+\\}");

  @Override
  public List<ValidationSuggestion> lint(OpenAPI openApi) {
    List<ValidationSuggestion> suggestions = new ArrayList<>();

    if (openApi.getPaths() == null) {
      return suggestions;
    }

    for (String path : openApi.getPaths().keySet()) {
      suggestions.addAll(validatePath(path));
    }

    return suggestions;
  }

  private List<ValidationSuggestion> validatePath(String path) {
    List<ValidationSuggestion> suggestions = new ArrayList<>();

    // Check for trailing slash
    if (path.endsWith("/") && !path.equals("/")) {
      suggestions.add(
          new ValidationSuggestion(
              String.format("Path '%s' should not have trailing slash.", path),
              "remove-trailing-slash",
              "warning",
              "general",
              Map.of("path", path, "issue", "trailing-slash"),
              true));
    }

    // Check for multiple consecutive slashes
    if (path.contains("//")) {
      suggestions.add(
          new ValidationSuggestion(
              String.format("Path '%s' should not contain consecutive slashes.", path),
              "fix-consecutive-slashes",
              "warning",
              "general",
              Map.of("path", path, "issue", "consecutive-slashes"),
              true));
    }

    // Check path segments for naming conventions
    String[] segments = path.split("/");
    for (int i = 1; i < segments.length; i++) { // Skip first empty segment
      String segment = segments[i];

      // Skip path parameters
      if (PATH_PARAMETER_PATTERN.matcher(segment).matches()) {
        continue;
      }

      // Skip empty segments
      if (segment.isEmpty()) {
        continue;
      }

      // Check for naming convention issues (prioritized to avoid duplicates)
      // Priority order: camelCase > underscores > general kebab-case

      if (segment.matches(".*[A-Z].*")) {
        // Has uppercase letters - camelCase issue
        suggestions.add(
            new ValidationSuggestion(
                String.format(
                    "Path segment '%s' in path '%s' should not use camelCase. Use kebab-case"
                        + " instead.",
                    segment, path),
                "convert-camelcase-to-kebab",
                "warning",
                "general",
                Map.of("path", path, "segment", segment, "issue", "camelcase-usage"),
                true));
      } else if (segment.contains("_")) {
        // Has underscores
        suggestions.add(
            new ValidationSuggestion(
                String.format(
                    "Path segment '%s' in path '%s' should use hyphens instead of underscores.",
                    segment, path),
                "replace-underscores-with-hyphens",
                "warning",
                "general",
                Map.of("path", path, "segment", segment, "issue", "underscore-usage"),
                true));
      } else if (!KEBAB_CASE_PATTERN.matcher(segment).matches()) {
        // Doesn't match kebab-case pattern (but no specific issue identified above)
        suggestions.add(
            new ValidationSuggestion(
                String.format(
                    "Path segment '%s' in path '%s' should use kebab-case (lowercase with"
                        + " hyphens).",
                    segment, path),
                "use-kebab-case",
                "warning",
                "general",
                Map.of("path", path, "segment", segment, "issue", "naming-convention"),
                true));
      }
    }

    // Check for proper resource naming (plural nouns)
    validateResourceNaming(path, suggestions);

    return suggestions;
  }

  private void validateResourceNaming(String path, List<ValidationSuggestion> suggestions) {
    String[] segments = path.split("/");

    for (int i = 1; i < segments.length; i++) {
      String segment = segments[i];

      // Skip path parameters and empty segments
      if (PATH_PARAMETER_PATTERN.matcher(segment).matches() || segment.isEmpty()) {
        continue;
      }

      // Check if this looks like a resource collection (not action/verb)
      // Resource collections should typically be plural
      if (isLikelyResourceCollection(segment, i, segments)) {
        if (isProbablySingular(segment)) {
          suggestions.add(
              new ValidationSuggestion(
                  String.format(
                      "Resource '%s' in path '%s' should likely be plural for collection"
                          + " endpoints.",
                      segment, path),
                  "use-plural-resource-names",
                  "info",
                  "general",
                  Map.of("path", path, "resource", segment, "issue", "singular-resource"),
                  true));
        }
      }
    }
  }

  private boolean isLikelyResourceCollection(String segment, int index, String[] segments) {
    // Simple heuristics to identify resource collections vs actions
    // Resources are typically followed by parameters or are at path end
    boolean followedByParameter =
        index + 1 < segments.length
            && PATH_PARAMETER_PATTERN.matcher(segments[index + 1]).matches();
    boolean isLastSegment = index == segments.length - 1;

    // Common action words that are not resources
    String[] commonActions = {"search", "validate", "export", "import", "sync", "health", "status"};
    for (String action : commonActions) {
      if (segment.equals(action)) {
        return false;
      }
    }

    return followedByParameter || isLastSegment;
  }

  private boolean isProbablySingular(String segment) {
    // Simple heuristics to detect potentially singular nouns
    // This is not perfect but covers common cases

    // Common plural endings
    if (segment.endsWith("s") || segment.endsWith("ies") || segment.endsWith("es")) {
      return false;
    }

    // Common irregular plurals
    String[] irregularPlurals = {
        "children", "people", "men", "women", "feet", "teeth", "mice", "data"
    };
    for (String plural : irregularPlurals) {
      if (segment.equals(plural)) {
        return false;
      }
    }

    // If it doesn't look plural, it might be singular
    return true;
  }
}
