package io.github.sharmanish.schemasculpt.config;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonInclude;
import io.swagger.v3.oas.models.media.Schema;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Primary;
import tools.jackson.databind.DeserializationFeature;
import tools.jackson.databind.SerializationFeature;
import tools.jackson.databind.cfg.DateTimeFeature;
import tools.jackson.databind.json.JsonMapper;

@Configuration
public class JacksonConfig {

  @Bean
  @Primary
  public JsonMapper jsonMapper() {
    return createBaseBuilder().build();
  }

  /** More aggressive configuration for specific use cases */
  @Bean("cleanJsonMapper")
  public JsonMapper cleanJsonMapper() {
    return createBaseBuilder().build();
  }

  /**
   * Centralized builder to ensure consistency across both beans. Jackson 3 modules (JavaTime, JDK8)
   * are auto-registered via findAndAddModules().
   */
  private JsonMapper.Builder createBaseBuilder() {
    return JsonMapper.builder()
        // 1. Module Management (replaces manual new JavaTimeModule())
        .findAndAddModules()

        // 2. Mix-ins
        .addMixIn(Schema.class, SchemaMixin.class)

        // 3. Inclusion Logic (The new functional API for Jackson 3)
        .changeDefaultPropertyInclusion(
            incl ->
                incl.withValueInclusion(JsonInclude.Include.NON_NULL)
                    .withContentInclusion(JsonInclude.Include.NON_NULL))

        // 4. Feature Management
        .disable(DateTimeFeature.WRITE_DATES_AS_TIMESTAMPS)
        .disable(SerializationFeature.FAIL_ON_EMPTY_BEANS)
        .disable(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES);
  }

  /** Mixin to ignore internal Swagger fields */
  public abstract static class SchemaMixin {
    @JsonIgnore
    abstract boolean getExampleSetFlag();

    @JsonIgnore
    abstract void setExampleSetFlag(boolean flag);
  }
}
