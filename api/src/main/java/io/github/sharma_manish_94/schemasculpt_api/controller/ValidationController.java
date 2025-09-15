package io.github.sharma_manish_94.schemasculpt_api.controller;

import io.github.sharma_manish_94.schemasculpt_api.dto.ValidationRequest;
import io.github.sharma_manish_94.schemasculpt_api.dto.ValidationResult;
import io.github.sharma_manish_94.schemasculpt_api.service.SessionService;
import io.github.sharma_manish_94.schemasculpt_api.service.ValidationService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v1")
public class ValidationController {

    private final ValidationService validationService;
    private final SessionService sessionService;

    public ValidationController(final ValidationService validationService,
                                final SessionService sessionService) {
        this.validationService = validationService;
        this.sessionService = sessionService;
    }

    @GetMapping("/health")
    public ResponseEntity<String> healthCheck() {
        return ResponseEntity.ok("Validation API is running");
    }

    @PostMapping("/validate")
    public ResponseEntity<ValidationResult> validateSpecification(
            @RequestBody ValidationRequest request
    ) {
        ValidationResult result = validationService.analyze(request.spec());
        return ResponseEntity.ok(result);
    }

    @PostMapping("/test-session")
    public ResponseEntity<String> createTestSession(@RequestBody String specText) {
        String sessionId = sessionService.createSession(specText);
        return ResponseEntity.ok("Session created with ID: " + sessionId);

    }
}
