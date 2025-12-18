package io.github.sharmanish.schemasculpt.config;

import java.util.List;

import com.fasterxml.jackson.annotation.JsonInclude;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.converter.HttpMessageConverter;
import org.springframework.http.converter.json.JacksonJsonHttpMessageConverter;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;
import tools.jackson.databind.DeserializationFeature;
import tools.jackson.databind.SerializationFeature;
import tools.jackson.databind.cfg.DateTimeFeature;
import tools.jackson.databind.json.JsonMapper;

@Configuration
public class WebMvcConfig implements WebMvcConfigurer {

  private final JsonMapper cleanJsonMapper;

  public WebMvcConfig(@Qualifier("cleanJsonMapper") JsonMapper cleanJsonMapper) {
      this.cleanJsonMapper = cleanJsonMapper;
  }


  @Bean(name = "cleanJsonMapper")
  public JsonMapper cleanJsonMapper() {
    return JsonMapper.builder()
            .changeDefaultPropertyInclusion(incl ->
                    incl.withValueInclusion(JsonInclude.Include.NON_NULL)
            )
            .disable(SerializationFeature.FAIL_ON_EMPTY_BEANS)
            .disable(DateTimeFeature.WRITE_DATES_AS_TIMESTAMPS)
            .disable(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES).findAndAddModules()
            .build();
  }

  @Override
  public void configureMessageConverters(List<HttpMessageConverter<?>> converters) {
    JacksonJsonHttpMessageConverter converter = new JacksonJsonHttpMessageConverter(cleanJsonMapper);
    converters.addFirst(converter);
  }
}