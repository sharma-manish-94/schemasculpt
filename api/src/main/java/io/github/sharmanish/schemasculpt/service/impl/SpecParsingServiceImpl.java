package io.github.sharmanish.schemasculpt.service.impl;

import io.github.sharmanish.schemasculpt.service.SpecParsingService;
import io.swagger.v3.parser.OpenAPIV3Parser;
import io.swagger.v3.parser.core.models.SwaggerParseResult;
import org.apache.commons.lang3.StringUtils;
import org.springframework.stereotype.Service;

@Service
public class SpecParsingServiceImpl implements SpecParsingService {
  @Override
  public SwaggerParseResult parse(final String specText) {
    if (StringUtils.isNotBlank(specText)) {
      return new OpenAPIV3Parser().readContents(specText);
    }
    return null;
  }
}
