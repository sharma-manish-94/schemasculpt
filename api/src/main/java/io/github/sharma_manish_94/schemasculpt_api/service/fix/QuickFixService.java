package io.github.sharma_manish_94.schemasculpt_api.service.fix;

import com.google.common.base.CaseFormat;
import io.github.sharma_manish_94.schemasculpt_api.dto.QuickFixRequest;
import io.github.sharma_manish_94.schemasculpt_api.service.SessionService;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.Operation;
import io.swagger.v3.oas.models.PathItem;
import org.springframework.stereotype.Service;

import java.util.regex.Pattern;

@Service
public class QuickFixService {

    private static final Pattern PATH_PARAM_PATTERN = Pattern.compile("\\{([^}]+)}");
    private final SessionService sessionService;

    public QuickFixService(SessionService sessionService) {
        this.sessionService = sessionService;
    }

    public OpenAPI applyFix(String sessionId, QuickFixRequest request) {
        OpenAPI openApi = sessionService.getSpecForSession(sessionId);
        if (openApi == null) {
            throw new IllegalArgumentException("Cannot apply fix to a null OpenAPI object.");
        }
        updateOpenAPI(request, openApi);
        sessionService.updateSessionSpec(sessionId, openApi);
        return openApi;
    }

    private void updateOpenAPI(QuickFixRequest request, OpenAPI openApi) {
        switch (request.ruleId()) {
            case "remove-unused-component":
                String componentName = (String) request.context().get("componentName");
                if (componentName != null && openApi.getComponents() != null && openApi.getComponents().getSchemas() != null) {
                    openApi.getComponents().getSchemas().remove(componentName);
                }
                break;
            case "generate-operation-id":
                String path = (String) request.context().get("path");
                String method = (String) request.context().get("method");
                if (path != null && method != null) {
                    generateOperationId(openApi, path, method);
                }
                break;
            case "use-https":
            case "use-https-for-production":
                String serverUrl = (String) request.context().get("serverUrl");
                Integer serverIndex = (Integer) request.context().get("serverIndex");
                if (serverUrl != null && serverIndex != null) {
                    fixHttpsUrl(openApi, serverIndex, serverUrl);
                }
                break;
            case "remove-trailing-slash":
                String pathToFix = (String) request.context().get("path");
                if (pathToFix != null) {
                    fixTrailingSlash(openApi, pathToFix);
                }
                break;
            case "fix-consecutive-slashes":
                String pathWithSlashes = (String) request.context().get("path");
                if (pathWithSlashes != null) {
                    fixConsecutiveSlashes(openApi, pathWithSlashes);
                }
                break;
            case "use-kebab-case":
            case "replace-underscores-with-hyphens":
            case "convert-camelcase-to-kebab":
                String originalPath = (String) request.context().get("path");
                String segment = (String) request.context().get("segment");
                if (originalPath != null && segment != null) {
                    fixPathNaming(openApi, originalPath, segment);
                }
                break;
            case "add-success-response":
                String opPath = (String) request.context().get("path");
                String opMethod = (String) request.context().get("method");
                if (opPath != null && opMethod != null) {
                    addSuccessResponse(openApi, opPath, opMethod);
                }
                break;
        }
    }

    private void generateOperationId(OpenAPI openApi, String path, String method) {
        PathItem pathItem = openApi.getPaths().get(path);
        if (pathItem == null) return;

        Operation operation = pathItem.readOperationsMap().get(PathItem.HttpMethod.valueOf(method.toUpperCase()));
        if (operation == null) return;

        // Build the new operationId (e.g., "getUsersById")
        String generatedId = buildIdFromPath(method.toLowerCase(), path);
        operation.setOperationId(generatedId);
    }

    private String buildIdFromPath(String method, String path) {
        String pathWithoutParams = PATH_PARAM_PATTERN.matcher(path)
                .replaceAll(match -> "By " + CaseFormat.LOWER_CAMEL.to(CaseFormat.UPPER_CAMEL, match.group(1)));

        String cleanPath = pathWithoutParams.replaceAll("[^a-zA-Z0-9 ]", " ").trim();

        return method.toLowerCase() + CaseFormat.LOWER_HYPHEN.to(CaseFormat.UPPER_CAMEL, cleanPath.replace(" ", "-"));
    }

    private void fixHttpsUrl(OpenAPI openApi, int serverIndex, String serverUrl) {
        if (openApi.getServers() != null && serverIndex < openApi.getServers().size()) {
            String httpsUrl = serverUrl.replaceFirst("^http://", "https://");
            openApi.getServers().get(serverIndex).setUrl(httpsUrl);
        }
    }

    private void fixTrailingSlash(OpenAPI openApi, String path) {
        if (openApi.getPaths() != null && openApi.getPaths().containsKey(path)) {
            String fixedPath = path.replaceAll("/+$", "");
            if (fixedPath.isEmpty()) {
                fixedPath = "/";
            }
            PathItem pathItem = openApi.getPaths().remove(path);
            openApi.getPaths().put(fixedPath, pathItem);
        }
    }

    private void fixConsecutiveSlashes(OpenAPI openApi, String path) {
        if (openApi.getPaths() != null && openApi.getPaths().containsKey(path)) {
            String fixedPath = path.replaceAll("/+", "/");
            PathItem pathItem = openApi.getPaths().remove(path);
            openApi.getPaths().put(fixedPath, pathItem);
        }
    }

    private void fixPathNaming(OpenAPI openApi, String originalPath, String segment) {
        if (openApi.getPaths() != null && openApi.getPaths().containsKey(originalPath)) {
            // Convert segment to kebab-case
            String fixedSegment = segment.toLowerCase()
                .replaceAll("_", "-") // Replace underscores with hyphens
                .replaceAll("([a-z])([A-Z])", "$1-$2") // Convert camelCase to kebab-case
                .toLowerCase();

            String fixedPath = originalPath.replace(segment, fixedSegment);
            PathItem pathItem = openApi.getPaths().remove(originalPath);
            openApi.getPaths().put(fixedPath, pathItem);
        }
    }

    private void addSuccessResponse(OpenAPI openApi, String path, String method) {
        PathItem pathItem = openApi.getPaths().get(path);
        if (pathItem == null) return;

        Operation operation = pathItem.readOperationsMap().get(PathItem.HttpMethod.valueOf(method.toUpperCase()));
        if (operation == null) return;

        if (operation.getResponses() == null) {
            operation.responses(new io.swagger.v3.oas.models.responses.ApiResponses());
        }

        // Add a default 200 response if no success response exists
        boolean hasSuccessResponse = operation.getResponses().keySet().stream()
            .anyMatch(code -> {
                try {
                    int statusCode = Integer.parseInt(code);
                    return statusCode >= 200 && statusCode < 400;
                } catch (NumberFormatException e) {
                    return false;
                }
            });

        if (!hasSuccessResponse) {
            io.swagger.v3.oas.models.responses.ApiResponse successResponse = new io.swagger.v3.oas.models.responses.ApiResponse();
            successResponse.setDescription("Successful operation");
            operation.getResponses().put("200", successResponse);
        }
    }

}
