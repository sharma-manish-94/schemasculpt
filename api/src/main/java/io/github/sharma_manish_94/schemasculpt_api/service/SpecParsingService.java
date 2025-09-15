package io.github.sharma_manish_94.schemasculpt_api.service;

import io.swagger.v3.parser.core.models.SwaggerParseResult;

public interface SpecParsingService {
	SwaggerParseResult parse(String specText);
}
