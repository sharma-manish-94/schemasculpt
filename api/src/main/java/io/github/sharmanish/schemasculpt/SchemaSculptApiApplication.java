package io.github.sharmanish.schemasculpt;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.DependsOn;

@SuppressWarnings("checkstyle:MissingJavadocType")
@SpringBootApplication
@DependsOn("flyway")
public class SchemaSculptApiApplication {

  private SchemaSculptApiApplication() {}

  public static void main(String[] args) {
    SpringApplication.run(SchemaSculptApiApplication.class, args);
  }
}
