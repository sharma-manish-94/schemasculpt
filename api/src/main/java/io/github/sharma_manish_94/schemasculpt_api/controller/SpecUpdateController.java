package io.github.sharma_manish_94.schemasculpt_api.controller;

import io.github.sharma_manish_94.schemasculpt_api.dto.request.UpdateOperationRequest;
import io.github.sharma_manish_94.schemasculpt_api.service.SessionService;
import io.github.sharma_manish_94.schemasculpt_api.service.SpecUpdateService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v1/sessions/{sessionId}/spec")
public class SpecUpdateController {
    private final SpecUpdateService specUpdateService;
    private final SessionService sessionService;

    public SpecUpdateController(final SpecUpdateService specUpdateService, final SessionService sessionService) {
        this.specUpdateService = specUpdateService;
        this.sessionService = sessionService;
    }

    @PutMapping
    public ResponseEntity<Void> updateFullSpec(@PathVariable String sessionId, @RequestBody String specText) {
        sessionService.updateSessionSpec(sessionId, specText);
        return ResponseEntity.ok().build();
    }

    @PatchMapping("/operations")
    public ResponseEntity<Void> updateOperation(@PathVariable String sessionId, @RequestBody UpdateOperationRequest request) {
        specUpdateService.updateOperation(sessionId, request);
        return ResponseEntity.ok().build();
    }
}
