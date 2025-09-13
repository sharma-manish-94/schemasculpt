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
public class OperationTagsRule implements LinterRule {
	
	@Override
	public List<ValidationSuggestion> lint(OpenAPI openApi) {
		List<ValidationSuggestion> suggestions = new ArrayList<>();
		if (openApi.getPaths() == null) {
			return suggestions;
		}
		
		for (Map.Entry<String, PathItem> pathEntry : openApi.getPaths().entrySet()) {
			String path = pathEntry.getKey();
			PathItem pathItem = pathEntry.getValue();
			
			for (Map.Entry<PathItem.HttpMethod, Operation> opEntry : pathItem.readOperationsMap().entrySet()) {
				PathItem.HttpMethod method = opEntry.getKey();
				Operation operation = opEntry.getValue();
				
				if (operation.getTags() == null || operation.getTags().isEmpty()) {
					suggestions.add(new ValidationSuggestion(
							String.format("Operation '%s %s' is missing tags for grouping.", method, path)
					));
				}
			}
		}
		return suggestions;
	}
}
