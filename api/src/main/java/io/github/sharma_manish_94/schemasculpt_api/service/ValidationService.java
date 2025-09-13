package io.github.sharma_manish_94.schemasculpt_api.service;

import io.github.sharma_manish_94.schemasculpt_api.dto.ValidationResult;

public interface ValidationService {
	ValidationResult analyze(String specText);
}
