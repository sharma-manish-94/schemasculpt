package io.github.sharmanish.schemasculpt.service;

import io.swagger.v3.parser.core.models.SwaggerParseResult;

public interface SpecParsingService {
  SwaggerParseResult parse(String specText);
}
