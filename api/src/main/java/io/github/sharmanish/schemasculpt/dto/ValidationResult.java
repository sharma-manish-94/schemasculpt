package io.github.sharmanish.schemasculpt.dto;

import java.util.List;

public record ValidationResult(
    List<ValidationError> errors, List<ValidationSuggestion> suggestions) {}
