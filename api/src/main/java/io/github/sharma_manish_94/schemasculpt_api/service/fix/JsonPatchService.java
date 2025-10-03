package io.github.sharma_manish_94.schemasculpt_api.service.fix;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.github.fge.jsonpatch.JsonPatch;
import com.github.fge.jsonpatch.JsonPatchException;
import io.github.sharma_manish_94.schemasculpt_api.dto.ai.JsonPatchOperation;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.parser.OpenAPIV3Parser;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.util.List;

/**
 * Service for applying JSON Patch (RFC 6902) operations to OpenAPI specifications.
 */
@Service
public class JsonPatchService {

    private static final Logger log = LoggerFactory.getLogger(JsonPatchService.class);
    private final ObjectMapper objectMapper;

    public JsonPatchService(ObjectMapper objectMapper) {
        this.objectMapper = objectMapper;
    }

    /**
     * Apply JSON Patch operations to an OpenAPI specification.
     *
     * @param openApi The OpenAPI specification to patch
     * @param patchOps The list of JSON Patch operations
     * @return The patched OpenAPI specification
     * @throws JsonPatchException if patch application fails
     */
    public OpenAPI applyPatch(OpenAPI openApi, List<JsonPatchOperation> patchOps) throws JsonPatchException {
        try {
            // Convert OpenAPI to JsonNode
            JsonNode specNode = objectMapper.valueToTree(openApi);

            // Convert patch operations to JsonNode
            JsonNode patchNode = objectMapper.valueToTree(patchOps);

            // Create JsonPatch from operations
            JsonPatch patch = JsonPatch.fromJson(patchNode);

            // Apply patch
            JsonNode patchedNode = patch.apply(specNode);

            // Convert back to OpenAPI
            String patchedJson = objectMapper.writeValueAsString(patchedNode);
            OpenAPI patchedOpenApi = new OpenAPIV3Parser().readContents(patchedJson).getOpenAPI();

            if (patchedOpenApi == null) {
                throw new IllegalStateException("Failed to parse patched OpenAPI specification");
            }

            log.info("Successfully applied {} patch operations", patchOps.size());
            return patchedOpenApi;

        } catch (Exception e) {
            log.error("Failed to apply JSON Patch: {}", e.getMessage());
            throw new JsonPatchException("Patch application failed: " + e.getMessage(), e);
        }
    }

    /**
     * Validate that patch operations can be applied to the spec without actually applying them.
     *
     * @param openApi The OpenAPI specification
     * @param patchOps The list of JSON Patch operations
     * @return true if patch can be applied, false otherwise
     */
    public boolean validatePatch(OpenAPI openApi, List<JsonPatchOperation> patchOps) {
        try {
            applyPatch(openApi, patchOps);
            return true;
        } catch (Exception e) {
            log.warn("Patch validation failed: {}", e.getMessage());
            return false;
        }
    }
}
