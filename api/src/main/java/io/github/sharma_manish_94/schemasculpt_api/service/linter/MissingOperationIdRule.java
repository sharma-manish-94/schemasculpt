package io.github.sharma_manish_94.schemasculpt_api.service.linter;

import io.github.sharma_manish_94.schemasculpt_api.dto.ValidationSuggestion;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.Operation;
import io.swagger.v3.oas.models.PathItem;
import org.springframework.stereotype.Component;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

@Component
public class MissingOperationIdRule implements LinterRule {
	@Override
	public List<ValidationSuggestion> lint(OpenAPI openApi) {
		List<ValidationSuggestion> suggestions = new ArrayList<>();
		if (openApi.getPaths() == null) {
			return suggestions;
		}
		
		for (Map.Entry<String, PathItem> pathEntry : openApi.getPaths().entrySet()) {
			String path = pathEntry.getKey();
			PathItem pathItem = pathEntry.getValue();
			
			// Iterate over each operation in the path (GET, POST, etc.)
			for (Map.Entry<PathItem.HttpMethod, Operation> opEntry : pathItem.readOperationsMap().entrySet()) {
				PathItem.HttpMethod method = opEntry.getKey();
				Operation operation = opEntry.getValue();
				
				if (operation.getOperationId() == null || operation.getOperationId().isBlank()) {
					suggestions.add(new ValidationSuggestion(
							String.format("Operation '%s %s' is missing an operationId.", method, path),
							"generate-operation-id",
							Map.of("path", path, "method", method.toString())
					));
				}
			}
		}
		return suggestions;
	}
}
