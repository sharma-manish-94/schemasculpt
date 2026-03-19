package io.github.sharmanish.schemasculpt;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.DependsOn;

@SuppressWarnings("checkstyle:MissingJavadocType")
@SpringBootApplication
@DependsOn("flyway")
public final class SchemaSculptApiApplication {

  private SchemaSculptApiApplication() {}

  /**
   * Entry point for the application.
   *
   * @param args command-line arguments
   */
  public static void main(String[] args) {
    SpringApplication.run(SchemaSculptApiApplication.class, args);
  }
}
