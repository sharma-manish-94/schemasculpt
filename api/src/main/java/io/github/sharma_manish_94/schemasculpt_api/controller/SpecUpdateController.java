package io.github.sharma_manish_94.schemasculpt_api.controller;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.github.sharma_manish_94.schemasculpt_api.dto.request.UpdateOperationRequest;
import io.github.sharma_manish_94.schemasculpt_api.service.SessionService;
import io.github.sharma_manish_94.schemasculpt_api.service.SpecUpdateService;
import io.github.sharma_manish_94.schemasculpt_api.service.TreeShakingService;
import io.swagger.v3.oas.models.OpenAPI;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v1/sessions/{sessionId}/spec")
@Slf4j
public class SpecUpdateController {
    private final SpecUpdateService specUpdateService;
    private final TreeShakingService treeShakingService;
    private final SessionService sessionService;
    private final ObjectMapper objectMapper;

    public SpecUpdateController(final SpecUpdateService specUpdateService,
                                final SessionService sessionService,
                                final TreeShakingService treeShakingService,
                                final ObjectMapper objectMapper) {
        this.specUpdateService = specUpdateService;
        this.sessionService = sessionService;
        this.treeShakingService = treeShakingService;
        this.objectMapper = objectMapper;
    }

    @PatchMapping("/operations")
    public ResponseEntity<Void> updateOperation(@PathVariable String sessionId,
                                                @RequestBody UpdateOperationRequest request) {
        specUpdateService.updateOperation(sessionId, request);
        return ResponseEntity.ok().build();
    }

    @GetMapping("/operations")
    public ResponseEntity<JsonNode> getOperationDetails(
            @PathVariable String sessionId,
            @RequestParam String path,
            @RequestParam String method
    ) {
        try {
            OpenAPI fullSpec = sessionService.getSpecForSession(sessionId);
            OpenAPI miniSpec = treeShakingService.extractOperationWithDependencies(fullSpec, path, method);
            if (null == miniSpec) {
                return ResponseEntity.notFound().build();
            }

            // Convert to JsonNode to ensure clean serialization without null fields
            JsonNode cleanJson = objectMapper.valueToTree(miniSpec);
            return ResponseEntity.ok(cleanJson);
        } catch (Exception e) {
            log.error("Error extracting operation details for session: {}, path: {}, method: {}",
                     sessionId, path, method, e);
            return ResponseEntity.internalServerError().build();
        }
    }
}
