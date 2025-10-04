package io.github.sharma_manish_94.schemasculpt_api.controller;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.github.sharma_manish_94.schemasculpt_api.dto.AIProxyRequest;
import io.github.sharma_manish_94.schemasculpt_api.dto.QuickFixRequest;
import io.github.sharma_manish_94.schemasculpt_api.dto.ValidationResult;
import io.github.sharma_manish_94.schemasculpt_api.service.SessionService;
import io.github.sharma_manish_94.schemasculpt_api.service.ValidationService;
import io.github.sharma_manish_94.schemasculpt_api.service.ai.AIService;
import io.github.sharma_manish_94.schemasculpt_api.service.fix.QuickFixService;
import io.github.sharma_manish_94.schemasculpt_api.util.OpenAPIEnumFixer;
import io.swagger.v3.core.util.Json;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.parser.OpenAPIV3Parser;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/v1/sessions/{sessionId}/spec")
@Slf4j
public class SpecificationController {
    private final SessionService sessionService;
    private final ValidationService validationService;
    private final QuickFixService quickFixService;
    private final AIService aiService;

    public SpecificationController(final SessionService sessionService,
                                   final ValidationService validationService,
                                   final QuickFixService quickFixService,
                                   final AIService aiService) {
        this.sessionService = sessionService;
        this.validationService = validationService;
        this.quickFixService = quickFixService;
        this.aiService = aiService;
    }

    @PostMapping("/validate")
    public ResponseEntity<ValidationResult> validateSpecification(@PathVariable String sessionId) {
        OpenAPI openAPI = sessionService.getSpecForSession(sessionId);
        ValidationResult validationResult = validationService.analyze(openAPI);
        return ResponseEntity.ok(validationResult);
    }

    @PostMapping("/fix")
    public ResponseEntity<Map<String, Object>> applyQuickFix(
            @PathVariable String sessionId,
            @RequestBody QuickFixRequest quickFixRequest) {
        OpenAPI updatedSpec = quickFixService.applyFix(sessionId, quickFixRequest);

        // CRITICAL: Convert to Map to avoid Swagger parser's uppercase enum issue
        Map<String, Object> fixedSpec = convertToMapWithFixedEnums(updatedSpec);

        return ResponseEntity.ok(fixedSpec);
    }

    @PostMapping("/transform")
    public ResponseEntity<Map<String, Object>> executeAIAction(
            @PathVariable String sessionId,
            @RequestBody AIProxyRequest request) {
        aiService.processSpecification(sessionId, request.prompt());
        OpenAPI updatedSpecObject = sessionService.getSpecForSession(sessionId);

        // CRITICAL: Convert to Map to avoid Swagger parser's uppercase enum issue
        Map<String, Object> fixedSpec = convertToMapWithFixedEnums(updatedSpecObject);

        return ResponseEntity.ok(fixedSpec);
    }

    /**
     * Convert OpenAPI object to Map with fixed lowercase enum values.
     * This avoids re-parsing through Swagger parser which converts enums to uppercase.
     */
    private Map<String, Object> convertToMapWithFixedEnums(OpenAPI openAPI) {
        try {
            // Serialize to JSON using Swagger's mapper
            String json = Json.pretty(openAPI);

            log.debug("Before enum fix - contains uppercase: {}",
                json.contains("OAUTH2") || json.contains("APIKEY") || json.contains("HTTP\""));

            // Fix all uppercase enums
            json = OpenAPIEnumFixer.fixEnums(json);

            log.debug("After enum fix - fixed to lowercase");

            // Parse to Map using Jackson (NOT Swagger parser to avoid re-uppercasing)
            ObjectMapper jacksonMapper = new ObjectMapper();
            return jacksonMapper.readValue(json, new TypeReference<Map<String, Object>>() {});

        } catch (Exception e) {
            log.error("Failed to convert OpenAPI to Map with fixed enums", e);
            throw new RuntimeException("Enum fixing failed", e);
        }
    }
}
