package io.github.sharma_manish_94.schemasculpt_api.service.fix;

import com.google.common.base.CaseFormat;
import io.github.sharma_manish_94.schemasculpt_api.dto.QuickFixRequest;
import io.swagger.v3.core.util.Json;
import io.swagger.v3.core.util.Yaml;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.Operation;
import io.swagger.v3.oas.models.PathItem;
import io.swagger.v3.parser.OpenAPIV3Parser;
import org.springframework.stereotype.Service;

import java.util.Objects;
import java.util.regex.Pattern;

@Service
public class QuickFixService {
	
	private static final Pattern PATH_PARAM_PATTERN = Pattern.compile("\\{([^}]+)}");
	
	public String applyFix(QuickFixRequest request) {
		OpenAPI openApi = new OpenAPIV3Parser().readContents(request.specText()).getOpenAPI();
		if (openApi == null) {
			return request.specText();
		}
		
		switch (request.ruleId()) {
			case "remove-unused-component":
				String componentName = (String) request.context().get("componentName");
				if (componentName != null && openApi.getComponents() != null && openApi.getComponents().getSchemas() != null) {
					openApi.getComponents().getSchemas().remove(componentName);
				}
				break;
			case "generate-operation-id":
				String path = (String) request.context().get("path");
				String method = (String) request.context().get("method");
				if (path != null && method != null) {
					generateOperationId(openApi, path, method);
				}
				break;
		}
		if (Objects.equals(request.format(), "json")) {
			return Json.pretty(openApi);
		} else {
			return Yaml.pretty(openApi); // Default to YAML
		}
	}
	
	private void generateOperationId(OpenAPI openApi, String path, String method) {
		PathItem pathItem = openApi.getPaths().get(path);
		if (pathItem == null) return;
		
		Operation operation = pathItem.readOperationsMap().get(PathItem.HttpMethod.valueOf(method.toUpperCase()));
		if (operation == null) return;
		
		// Build the new operationId (e.g., "getUsersById")
		String generatedId = buildIdFromPath(method.toLowerCase(), path);
		operation.setOperationId(generatedId);
	}
	
	private String buildIdFromPath(String method, String path) {
		String pathWithoutParams = PATH_PARAM_PATTERN.matcher(path)
				                           .replaceAll(match -> "By " + CaseFormat.LOWER_CAMEL.to(CaseFormat.UPPER_CAMEL, match.group(1)));
		
		String cleanPath = pathWithoutParams.replaceAll("[^a-zA-Z0-9 ]", " ").trim();
		
		return method.toLowerCase() + CaseFormat.LOWER_HYPHEN.to(CaseFormat.UPPER_CAMEL, cleanPath.replace(" ", "-"));
	}
	
}
