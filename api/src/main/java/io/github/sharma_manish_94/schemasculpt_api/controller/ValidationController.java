package io.github.sharma_manish_94.schemasculpt_api.controller;

import io.github.sharma_manish_94.schemasculpt_api.dto.ValidationError;
import io.github.sharma_manish_94.schemasculpt_api.dto.ValidationRequest;
import io.github.sharma_manish_94.schemasculpt_api.dto.ValidationResult;
import io.github.sharma_manish_94.schemasculpt_api.service.ValidationService;
import io.swagger.v3.parser.OpenAPIV3Parser;
import io.swagger.v3.parser.core.models.SwaggerParseResult;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/v1")
@CrossOrigin(origins = "http://localhost:3000")
public class ValidationController {
	
	private final ValidationService validationService;
	
	public ValidationController(final ValidationService validationService) {
		this.validationService = validationService;
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
}
