package io.github.sharma_manish_94.schemasculpt_api.service.fix;

import io.github.sharma_manish_94.schemasculpt_api.dto.QuickFixRequest;
import io.swagger.v3.core.util.Json;
import io.swagger.v3.core.util.Yaml;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.parser.OpenAPIV3Parser;
import org.springframework.stereotype.Service;

import java.util.Objects;

@Service
public class QuickFixService {
	
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
			// Future cases for other rules would go here
		}
		if (Objects.equals(request.format(), "json")) {
			return Json.pretty(openApi);
		} else {
			return Yaml.pretty(openApi); // Default to YAML
		}
	}
	
}
