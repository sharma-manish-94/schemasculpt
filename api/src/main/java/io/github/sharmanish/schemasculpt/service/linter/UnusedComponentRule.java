package io.github.sharmanish.schemasculpt.service.linter;

import io.github.sharmanish.schemasculpt.dto.ValidationSuggestion;
import io.swagger.v3.oas.models.OpenAPI;
import java.util.Collections;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import org.springframework.stereotype.Component;
import tools.jackson.core.JacksonException;
import tools.jackson.databind.json.JsonMapper;

@Component
public class UnusedComponentRule implements LinterRule {

  private static final Pattern REF_PATTERN =
      Pattern.compile("\"\\$ref\":\\s*\"#/components/schemas/([^\"]+)\"");
  private final JsonMapper jsonMapper = new JsonMapper();

  @Override
  public List<ValidationSuggestion> lint(OpenAPI openApi) {
    if (openApi.getComponents() == null || openApi.getComponents().getSchemas() == null) {
      return Collections.emptyList();
    }

    Set<String> definedSchemas = openApi.getComponents().getSchemas().keySet();
    Set<String> referencedSchemas = new HashSet<>();

    try {
      String jsonString = jsonMapper.writeValueAsString(openApi);
      Matcher matcher = REF_PATTERN.matcher(jsonString);
      while (matcher.find()) {
        referencedSchemas.add(matcher.group(1));
      }
    } catch (JacksonException e) {
      // If we can't process the spec, we can't find references.
      return Collections.emptyList();
    }

    return definedSchemas.stream()
        .filter(defined -> !referencedSchemas.contains(defined))
        .map(
            unused ->
                new ValidationSuggestion(
                    "Component schema '" + unused + "' is defined but never used.",
                    "remove-unused-component",
                    "warning",
                    "performance",
                    Map.of("componentName", unused),
                    true))
        .toList();
  }
}
