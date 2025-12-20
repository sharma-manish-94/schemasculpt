package io.github.sharmanish.schemasculpt.config;

import java.util.List;

import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.converter.HttpMessageConverter;
import org.springframework.http.converter.json.JacksonJsonHttpMessageConverter;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;
import tools.jackson.databind.json.JsonMapper;

@Configuration
public class WebMvcConfig implements WebMvcConfigurer {

  private final JsonMapper cleanJsonMapper;

  public WebMvcConfig(@Qualifier("cleanJsonMapper") JsonMapper cleanJsonMapper) {
      this.cleanJsonMapper = cleanJsonMapper;
  }

  @Override
  public void configureMessageConverters(List<HttpMessageConverter<?>> converters) {
    JacksonJsonHttpMessageConverter converter = new JacksonJsonHttpMessageConverter(cleanJsonMapper);
    converters.addFirst(converter);
  }
}
