package io.github.sharma_manish_94.schemasculpt_api.controller;

import io.github.sharma_manish_94.schemasculpt_api.dto.AIProxyRequest;
import io.github.sharma_manish_94.schemasculpt_api.dto.QuickFixRequest;
import io.github.sharma_manish_94.schemasculpt_api.dto.ValidationResult;
import io.github.sharma_manish_94.schemasculpt_api.service.SessionService;
import io.github.sharma_manish_94.schemasculpt_api.service.ValidationService;
import io.github.sharma_manish_94.schemasculpt_api.service.ai.AIService;
import io.github.sharma_manish_94.schemasculpt_api.service.fix.QuickFixService;
import io.swagger.v3.oas.models.OpenAPI;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v1/sessions/{sessionId}/spec")
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
    public ResponseEntity<OpenAPI> applyQuickFix(
            @PathVariable String sessionId,
            @RequestBody QuickFixRequest quickFixRequest) {
        OpenAPI updatedSpec = quickFixService.applyFix(sessionId, quickFixRequest);
        return ResponseEntity.ok(updatedSpec);
    }

    @PostMapping("/transform")
    public ResponseEntity<OpenAPI> executeAIAction(
            @PathVariable String sessionId,
            @RequestBody AIProxyRequest request) {
        aiService.processSpecification(sessionId, request.prompt());
        OpenAPI updatedSpecObject = sessionService.getSpecForSession(sessionId);
        return ResponseEntity.ok(updatedSpecObject);
    }
}
