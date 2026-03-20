package io.github.sharmanish.schemasculpt.controller;

import io.github.sharmanish.schemasculpt.dto.request.UpdateOperationRequest;
import io.github.sharmanish.schemasculpt.service.SessionService;
import io.github.sharmanish.schemasculpt.service.SpecUpdateService;
import io.github.sharmanish.schemasculpt.service.TreeShakingService;
import io.github.sharmanish.schemasculpt.util.LogSanitizer;
import io.swagger.v3.oas.models.OpenAPI;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import tools.jackson.databind.JsonNode;
import tools.jackson.databind.json.JsonMapper;

@RestController
@RequestMapping("/api/v1/sessions/{sessionId}/spec")
@Slf4j
public class SpecUpdateController {
  private final SpecUpdateService specUpdateService;
  private final TreeShakingService treeShakingService;
  private final SessionService sessionService;
  private final JsonMapper jsonMapper;

  public SpecUpdateController(
      final SpecUpdateService specUpdateService,
      final SessionService sessionService,
      final TreeShakingService treeShakingService,
      final JsonMapper jsonMapper) {
    this.specUpdateService = specUpdateService;
    this.sessionService = sessionService;
    this.treeShakingService = treeShakingService;
    this.jsonMapper = jsonMapper;
  }

  @PatchMapping("/operations")
  public ResponseEntity<Void> updateOperation(
      @PathVariable String sessionId, @RequestBody UpdateOperationRequest request) {
    specUpdateService.updateOperation(sessionId, request);
    return ResponseEntity.ok().build();
  }

  @GetMapping("/operations")
  public ResponseEntity<JsonNode> getOperationDetails(
      @PathVariable String sessionId, @RequestParam String path, @RequestParam String method) {
    try {
      OpenAPI fullSpec = sessionService.getSpecForSession(sessionId);
      OpenAPI miniSpec =
          treeShakingService.extractOperationWithDependencies(fullSpec, path, method);
      if (null == miniSpec) {
        return ResponseEntity.notFound().build();
      }

      // Convert to JsonNode to ensure clean serialization without null fields
      JsonNode cleanJson = jsonMapper.valueToTree(miniSpec);
      return ResponseEntity.ok(cleanJson);
    } catch (Exception e) {
      log.error(
          "Error extracting operation details for session: {}, path: {}, method: {}",
          LogSanitizer.sanitize(sessionId),
          LogSanitizer.sanitize(path),
          LogSanitizer.sanitize(method),
          e);
      return ResponseEntity.internalServerError().build();
    }
  }
}
