package io.github.sharma_manish_94.schemasculpt_api.service.linter;

import io.github.sharma_manish_94.schemasculpt_api.dto.ValidationSuggestion;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.servers.Server;
import org.springframework.stereotype.Component;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

/**
 * Linter rule that ensures server URLs use HTTPS for security.
 * Helps identify potential security vulnerabilities with HTTP endpoints.
 */
@Component
public class HttpsOnlyRule implements LinterRule {

    @Override
    public List<ValidationSuggestion> lint(OpenAPI openApi) {
        List<ValidationSuggestion> suggestions = new ArrayList<>();

        if (openApi.getServers() == null || openApi.getServers().isEmpty()) {
            suggestions.add(new ValidationSuggestion(
                "API should define at least one server URL.",
                "add-server-url",
                Map.of("location", "servers")
            ));
            return suggestions;
        }

        for (int i = 0; i < openApi.getServers().size(); i++) {
            Server server = openApi.getServers().get(i);
            String serverUrl = server.getUrl();

            if (serverUrl != null && !isSecureUrl(serverUrl)) {
                // Check if this might be a development/localhost server
                if (isDevelopmentServer(serverUrl)) {
                    suggestions.add(new ValidationSuggestion(
                        String.format("Server URL '%s' uses HTTP. Consider using HTTPS for production environments.",
                            serverUrl),
                        "use-https-for-production",
                        Map.of("serverUrl", serverUrl, "serverIndex", i, "severity", "warning")
                    ));
                } else {
                    suggestions.add(new ValidationSuggestion(
                        String.format("Server URL '%s' should use HTTPS for security.",
                            serverUrl),
                        "use-https",
                        Map.of("serverUrl", serverUrl, "serverIndex", i, "severity", "error")
                    ));
                }
            }

            // Check for mixed protocols (some HTTPS, some HTTP)
            if (serverUrl != null && hasMultipleProtocols(openApi.getServers())) {
                suggestions.add(new ValidationSuggestion(
                    "API defines servers with mixed protocols (HTTP and HTTPS). Consider using HTTPS consistently.",
                    "consistent-https-usage",
                    Map.of("issue", "mixed-protocols")
                ));
                break; // Only show this warning once
            }
        }

        return suggestions;
    }

    private boolean isSecureUrl(String url) {
        // Check if URL starts with HTTPS
        return url.toLowerCase().startsWith("https://");
    }

    private boolean isDevelopmentServer(String url) {
        String lowerUrl = url.toLowerCase();
        return lowerUrl.contains("localhost") ||
               lowerUrl.contains("127.0.0.1") ||
               lowerUrl.contains("0.0.0.0") ||
               lowerUrl.matches(".*://[^/]*\\.(dev|test|local|staging)([:/].*)?");
    }

    private boolean hasMultipleProtocols(List<Server> servers) {
        boolean hasHttp = false;
        boolean hasHttps = false;

        for (Server server : servers) {
            String url = server.getUrl();
            if (url != null) {
                if (url.toLowerCase().startsWith("http://")) {
                    hasHttp = true;
                } else if (url.toLowerCase().startsWith("https://")) {
                    hasHttps = true;
                }
            }
        }

        return hasHttp && hasHttps;
    }
}