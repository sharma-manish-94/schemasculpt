package io.github.sharma_manish_94.schemasculpt_api.config;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import io.swagger.v3.oas.models.media.Schema;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Primary;

@Configuration
public class JacksonConfig {

  /** Mixin to ignore internal Swagger fields */
  public abstract static class SchemaMixin {
    @JsonIgnore
    abstract boolean getExampleSetFlag();

    @JsonIgnore
    abstract void setExampleSetFlag(boolean flag);
  }

  @Bean
  @Primary
  public ObjectMapper objectMapper() {
    ObjectMapper mapper = new ObjectMapper();

    // Register JavaTimeModule for Java 8 date/time support
    mapper.registerModule(new JavaTimeModule());

    // Add mixin to ignore internal Swagger fields
    mapper.addMixIn(Schema.class, SchemaMixin.class);

    // Exclude null values - most important setting
    mapper.setSerializationInclusion(JsonInclude.Include.NON_NULL);
    mapper.setDefaultPropertyInclusion(
        JsonInclude.Value.construct(JsonInclude.Include.NON_NULL, JsonInclude.Include.NON_NULL));

    // Disable problematic features
    mapper.disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS);
    mapper.disable(SerializationFeature.FAIL_ON_EMPTY_BEANS);
    mapper.disable(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES);

    // CRITICAL: DO NOT enable WRITE_ENUMS_USING_TO_STRING
    // This causes OpenAPI enums to serialize as uppercase (OAUTH2, APIKEY, HEADER)
    // instead of the correct lowercase values (oauth2, apiKey, header)
    // mapper.enable(SerializationFeature.WRITE_ENUMS_USING_TO_STRING);

    return mapper;
  }

  /** Alternative configuration that's more aggressive about excluding nulls */
  @Bean("cleanObjectMapper")
  public ObjectMapper cleanObjectMapper() {
    ObjectMapper mapper = new ObjectMapper();

    // Register JavaTimeModule for Java 8 date/time support
    mapper.registerModule(new JavaTimeModule());

    // Add mixin to ignore internal Swagger fields
    mapper.addMixIn(Schema.class, SchemaMixin.class);

    // Most aggressive null exclusion
    mapper.setSerializationInclusion(JsonInclude.Include.NON_NULL);
    mapper.setDefaultPropertyInclusion(
        JsonInclude.Value.construct(JsonInclude.Include.NON_NULL, JsonInclude.Include.NON_NULL));

    // Disable problematic features
    mapper.disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS);
    mapper.disable(SerializationFeature.FAIL_ON_EMPTY_BEANS);
    mapper.disable(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES);

    return mapper;
  }
}
