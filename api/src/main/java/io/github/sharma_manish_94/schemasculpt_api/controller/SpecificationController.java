package io.github.sharma_manish_94.schemasculpt_api.controller;

import io.github.sharma_manish_94.schemasculpt_api.dto.*;
import io.github.sharma_manish_94.schemasculpt_api.service.ValidationService;
import io.github.sharma_manish_94.schemasculpt_api.service.ai.AIService;
import io.github.sharma_manish_94.schemasculpt_api.service.fix.QuickFixService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import reactor.core.publisher.Mono;

@RestController
@RequestMapping("/api/v1/specifications")
public class SpecificationController {
    private final ValidationService validationService;
    private final QuickFixService quickFixService;
    private final AIService aiService;

    public SpecificationController(final ValidationService validationService, final QuickFixService quickFixService, final AIService aiService) {
        this.validationService = validationService;
        this.quickFixService = quickFixService;
        this.aiService = aiService;
    }

    @PostMapping("/validate")
    public ResponseEntity<ValidationResult> validateSpecification(@RequestBody String specText) {
        ValidationResult validationResult = validationService.analyze(specText);
        return ResponseEntity.ok(validationResult);
    }

    @PostMapping("/fix")
    public ResponseEntity<QuickFixResponse> applyQuickFix(@RequestBody QuickFixRequest quickFixRequest) {
        String updatedSpec = quickFixService.applyFix(quickFixRequest);
        return ResponseEntity.ok(new QuickFixResponse(updatedSpec));
    }
    
    @PostMapping("/transform")
    public Mono<AIResponse> executeAIAction(@RequestBody AIRequest aiRequest) {
        return aiService.processSpecification(aiRequest.specText(), aiRequest.prompt())
                .map(AIResponse::new);
    }
}
