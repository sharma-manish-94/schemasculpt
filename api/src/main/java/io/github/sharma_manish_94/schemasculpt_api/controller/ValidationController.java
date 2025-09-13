package io.github.sharma_manish_94.schemasculpt_api.controller;

import io.github.sharma_manish_94.schemasculpt_api.dto.ValidationError;
import io.github.sharma_manish_94.schemasculpt_api.dto.ValidationRequest;
import io.swagger.v3.parser.OpenAPIV3Parser;
import io.swagger.v3.parser.core.models.SwaggerParseResult;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/v1")
@CrossOrigin(origins = "http://localhost:3000")
public class ValidationController {
	
	@GetMapping("/health")
	public ResponseEntity<String> healthCheck() {
		return ResponseEntity.ok("Validation API is running");
	}
	
	@PostMapping("/validate")
	public ResponseEntity<List<ValidationError>> validateSpecification(
			@RequestBody ValidationRequest request
	) {
		SwaggerParseResult result = new OpenAPIV3Parser().readContents(request.spec());
		final List<ValidationError> errors = result.getMessages().stream().map(ValidationError::new).toList();
		return ResponseEntity.ok(errors);
	}
}
