package io.github.sharmanish.schemasculpt;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SuppressWarnings("checkstyle:MissingJavadocType")
@SpringBootApplication
public class SchemaSculptApiApplication {

  private SchemaSculptApiApplication() {}

  static void main(String[] args) {
    SpringApplication.run(SchemaSculptApiApplication.class, args);
  }
}
