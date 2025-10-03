package io.github.sharma_manish_94.schemasculpt_api.service.fix;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.github.fge.jsonpatch.JsonPatchException;
import com.google.common.base.CaseFormat;
import io.github.sharma_manish_94.schemasculpt_api.dto.QuickFixRequest;
import io.github.sharma_manish_94.schemasculpt_api.dto.ai.PatchGenerationRequest;
import io.github.sharma_manish_94.schemasculpt_api.dto.ai.PatchGenerationResponse;
import io.github.sharma_manish_94.schemasculpt_api.service.SessionService;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.Operation;
import io.swagger.v3.oas.models.PathItem;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;

import java.util.Arrays;
import java.util.HashSet;
import java.util.Set;
import java.util.regex.Pattern;

@Service
public class QuickFixService {

    private static final Logger log = LoggerFactory.getLogger(QuickFixService.class);
    private static final Pattern PATH_PARAM_PATTERN = Pattern.compile("\\{([^}]+)}");

    // Rules that can be fixed automatically without AI
    private static final Set<String> AUTO_FIXABLE_RULES = new HashSet<>(Arrays.asList(
            "remove-unused-component",
            "generate-operation-id",
            "use-https",
            "use-https-for-production",
            "remove-trailing-slash",
            "fix-consecutive-slashes",
            "use-kebab-case",
            "replace-underscores-with-hyphens",
            "convert-camelcase-to-kebab",
            "add-success-response"
    ));

    private final SessionService sessionService;
    private final JsonPatchService jsonPatchService;
    private final ObjectMapper objectMapper;
    private final WebClient aiServiceClient;

    public QuickFixService(
            SessionService sessionService,
            JsonPatchService jsonPatchService,
            ObjectMapper objectMapper,
            @Value("${ai.service.url:http://localhost:8000}") String aiServiceUrl
    ) {
        this.sessionService = sessionService;
        this.jsonPatchService = jsonPatchService;
        this.objectMapper = objectMapper;
        this.aiServiceClient = WebClient.builder()
                .baseUrl(aiServiceUrl)
                .build();
    }

    public OpenAPI applyFix(String sessionId, QuickFixRequest request) {
        OpenAPI openApi = sessionService.getSpecForSession(sessionId);
        if (openApi == null) {
            throw new IllegalArgumentException("Cannot apply fix to a null OpenAPI object.");
        }

        // Check if this is an auto-fixable rule
        if (AUTO_FIXABLE_RULES.contains(request.ruleId())) {
            log.info("Applying auto-fix for rule: {}", request.ruleId());
            updateOpenAPI(request, openApi);
        } else {
            // Use AI service with JSON Patch approach
            log.info("Applying AI-powered fix for rule: {}", request.ruleId());
            openApi = applyAIFix(openApi, request);
        }

        sessionService.updateSessionSpec(sessionId, openApi);
        return openApi;
    }

    /**
     * Apply AI-powered fix using JSON Patch (RFC 6902).
     * The AI service generates precise patch operations instead of the full spec.
     */
    private OpenAPI applyAIFix(OpenAPI openApi, QuickFixRequest request) {
        try {
            // Convert OpenAPI to JSON string
            String specJson = objectMapper.writeValueAsString(openApi);

            // Create request for AI service
            PatchGenerationRequest patchRequest = new PatchGenerationRequest(
                    specJson,
                    request.ruleId(),
                    request.context(),
                    "Generated fix for: " + request.ruleId()
            );

            // Call AI service to generate JSON Patch
            PatchGenerationResponse patchResponse = aiServiceClient
                    .post()
                    .uri("/ai/patch/generate")
                    .bodyValue(patchRequest)
                    .retrieve()
                    .bodyToMono(PatchGenerationResponse.class)
                    .block();

            if (patchResponse == null || patchResponse.patches().isEmpty()) {
                log.warn("AI service returned no patch operations for rule: {}", request.ruleId());
                return openApi; // Return unchanged
            }

            log.info("AI service generated {} patch operations with confidence: {}",
                    patchResponse.patches().size(), patchResponse.confidence());

            // Apply the JSON Patch operations
            OpenAPI patchedSpec = jsonPatchService.applyPatch(openApi, patchResponse.patches());

            log.info("Successfully applied AI-generated patch. Explanation: {}", patchResponse.explanation());
            return patchedSpec;

        } catch (JsonPatchException e) {
            log.error("Failed to apply AI-generated patch: {}", e.getMessage());
            throw new RuntimeException("AI fix failed: " + e.getMessage(), e);
        } catch (Exception e) {
            log.error("AI service call failed: {}", e.getMessage());
            throw new RuntimeException("AI service error: " + e.getMessage(), e);
        }
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
            String fixedSegment = segment
                    .replaceAll("([a-z])([A-Z])", "$1-$2") // Convert camelCase to kebab-case first
                    .replaceAll("_", "-") // Replace underscores with hyphens
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
