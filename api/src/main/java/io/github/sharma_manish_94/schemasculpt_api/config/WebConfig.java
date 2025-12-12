package io.github.sharma_manish_94.schemasculpt_api.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.EnableWebMvc;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

/**
 * Configuration class for setting up CORS (Cross-Origin Resource Sharing) in the application.
 *
 * <p>Reads allowed origins from the application properties and configures CORS mappings for API
 * endpoints under <code>/api/**</code>.
 *
 * <p>The allowed origins are specified via the <code>app.cors.allowed-origins</code> property.
 * Localhost patterns are also allowed for development purposes.
 */
@Configuration
@EnableWebMvc
public class WebConfig implements WebMvcConfigurer {

  /**
   * Comma-separated list of allowed origins for CORS, injected from application properties.
   */
  @Value("${app.cors.allowed-origins}")
  private String allowedOrigins;

  /**
   * Configures CORS mappings for API endpoints.
   *
   * @param corsRegistry the {@link CorsRegistry} to configure
   */
  @Override
  public void addCorsMappings(final CorsRegistry corsRegistry) {
    String[] origins = allowedOrigins.split(",");
    corsRegistry
        .addMapping("/api/**")
        .allowedOriginPatterns("http://localhost:*", "http://127.0.0.1:*")
        .allowedOrigins(origins)
        .allowedMethods("GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS")
        .allowedHeaders("*")
        .allowCredentials(false) // Set to false to allow pattern matching
        .maxAge(3600);
  }
}
