package io.github.sharma_manish_94.schemasculpt_api.controller;

import io.github.sharma_manish_94.schemasculpt_api.dto.request.UpdateOperationRequest;
import io.github.sharma_manish_94.schemasculpt_api.service.SpecUpdateService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v1/sessions/{sessionId}/spec")
public class SpecUpdateController {
    private final SpecUpdateService specUpdateService;

    public SpecUpdateController(final SpecUpdateService specUpdateService) {
        this.specUpdateService = specUpdateService;
    }

    @PatchMapping("/operations")
    public ResponseEntity<Void> updateOperation(
            @PathVariable String sessionId,
            @RequestBody UpdateOperationRequest request) {
        specUpdateService.updateOperation(sessionId, request);
        return ResponseEntity.ok().build();
    }
}
