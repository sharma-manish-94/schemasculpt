package io.github.sharmanish.schemasculpt.service;

import io.github.sharmanish.schemasculpt.dto.ValidationResult;
import io.swagger.v3.oas.models.OpenAPI;

public interface ValidationService {
  ValidationResult analyze(String specText);

  ValidationResult analyze(OpenAPI openApi);
}
