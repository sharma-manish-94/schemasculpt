package io.github.sharma_manish_94.schemasculpt_api.controller;

import com.fasterxml.jackson.core.JsonProcessingException;
import io.github.sharma_manish_94.schemasculpt_api.dto.QuickFixRequest;
import io.github.sharma_manish_94.schemasculpt_api.dto.QuickFixResponse;
import io.github.sharma_manish_94.schemasculpt_api.service.fix.QuickFixService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v1")
public class QuickFixController {
	
	private final QuickFixService quickFixService;
	
	public QuickFixController(QuickFixService quickFixService) {
		this.quickFixService = quickFixService;
	}
	
	@PostMapping("/fix")
	public ResponseEntity<QuickFixResponse> applyQuickFix(@RequestBody QuickFixRequest quickFixRequest) throws JsonProcessingException {
		final String updatedSpec = quickFixService.applyFix(quickFixRequest);
		return ResponseEntity.ok(new QuickFixResponse(updatedSpec));
	}
}
