package io.github.sharmanish.schemasculpt.service.linter;

import io.github.sharmanish.schemasculpt.dto.ValidationSuggestion;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.servers.Server;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import org.springframework.stereotype.Component;

/**
 * Linter rule that ensures server URLs use HTTPS for security. Helps identify potential security
 * vulnerabilities with HTTP endpoints.
 */
@Component
public class HttpsOnlyRule implements LinterRule {

  @Override
  public List<ValidationSuggestion> lint(OpenAPI openApi) {
    List<ValidationSuggestion> suggestions = new ArrayList<>();

    if (openApi.getServers() == null || openApi.getServers().isEmpty()) {
      suggestions.add(
          new ValidationSuggestion(
              "API should define at least one server URL.",
              "add-server-url",
              "warning",
              "completeness",
              Map.of("location", "servers"),
              true));
      return suggestions;
    }

    for (int i = 0; i < openApi.getServers().size(); i++) {
      Server server = openApi.getServers().get(i);
      String serverUrl = server.getUrl();

      if (serverUrl != null && !isSecureUrl(serverUrl)) {
        // Check if this might be a development/localhost server
        if (isDevelopmentServer(serverUrl)) {
          suggestions.add(
              new ValidationSuggestion(
                  String.format(
                      "Server URL '%s' uses HTTP. Consider using HTTPS for"
                          + " production environments.",
                      serverUrl),
                  "use-https-for-production",
                  "warning",
                  "security",
                  Map.of("serverUrl", serverUrl, "serverIndex", i),
                  true));
        } else {
          suggestions.add(
              new ValidationSuggestion(
                  String.format("Server URL '%s' should use HTTPS for security.", serverUrl),
                  "use-https",
                  "error",
                  "security",
                  Map.of("serverUrl", serverUrl, "serverIndex", i),
                  true));
        }
      }

      // Check for mixed protocols (some HTTPS, some HTTP)
      if (serverUrl != null && hasMultipleProtocols(openApi.getServers())) {
        suggestions.add(
            new ValidationSuggestion(
                "API defines servers with mixed protocols (HTTP and HTTPS)."
                    + " Consider using HTTPS consistently.",
                "consistent-https-usage",
                "warning",
                "security",
                Map.of("issue", "mixed-protocols"),
                true));
        break; // Only show this warning once
      }
    }

    return suggestions;
  }

  private boolean isSecureUrl(String url) {
    // Check if URL starts with HTTPS
    return url.toLowerCase(Locale.ROOT).startsWith("https://");
  }

  private boolean isDevelopmentServer(String url) {
    String lowerUrl = url.toLowerCase(Locale.ROOT);
    return lowerUrl.contains("localhost")
        || lowerUrl.contains("127.0.0.1")
        || lowerUrl.contains("0.0.0.0")
        || lowerUrl.matches(".*://[^/]*\\.(dev|test|local|staging)([:/].*)?");
  }

  private boolean hasMultipleProtocols(List<Server> servers) {
    boolean hasHttp = false;
    boolean hasHttps = false;

    for (Server server : servers) {
      String url = server.getUrl();
      if (url != null) {
        if (url.toLowerCase(Locale.ROOT).startsWith("http://")) {
          hasHttp = true;
        } else if (url.toLowerCase(Locale.ROOT).startsWith("https://")) {
          hasHttps = true;
        }
      }
    }

    return hasHttp && hasHttps;
  }
}
