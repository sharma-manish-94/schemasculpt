package io.github.sharma_manish_94.schemasculpt_api.service;

import io.github.sharma_manish_94.schemasculpt_api.dto.ValidationResult;
import io.swagger.v3.oas.models.OpenAPI;

public interface ValidationService {
  ValidationResult analyze(String specText);

  ValidationResult analyze(OpenAPI openApi);
}
