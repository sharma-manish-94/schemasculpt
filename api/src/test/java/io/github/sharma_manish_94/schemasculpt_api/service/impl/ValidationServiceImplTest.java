package io.github.sharma_manish_94.schemasculpt_api.service.impl;

import static org.assertj.core.api.Assertions.assertThat;

import io.github.sharma_manish_94.schemasculpt_api.dto.ValidationResult;
import io.github.sharma_manish_94.schemasculpt_api.service.ValidationService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

@SpringBootTest
class ValidationServiceImplTest {

  @Autowired private ValidationService validationService;

  @Test
  void whenSpecHasUnusedComponent_thenSuggestionIsFound() {
    String specWithUnusedComponent =
        """
                openapi: 3.0.0
                info:
                  title: API with Unused Component
                  version: 1.0.0
                paths:
                  /test:
                    get:
                      summary: An endpoint
                      responses:
                        '200':
                          description: OK
                components:
                  schemas:
                    UnusedSchema:
                      type: object
                """;

    ValidationResult validationResult = validationService.analyze(specWithUnusedComponent);
    assertThat(validationResult).isNotNull();
    assertThat(validationResult.errors()).isEmpty();
    assertThat(validationResult.suggestions()).hasSize(10);
  }

  @Test
  void whenSpecIsInvalid_thenErrorIsFound() {
    String invalidSpec =
        """
                openapi: 3.0.0
                info:
                  title: Invalid API
                  version 1.0.0
                paths:
                  /test:
                    get:
                      summary: An endpoint
                      responses:
                        '200':
                          description: OK
                """;

    ValidationResult validationResult = validationService.analyze(invalidSpec);
    assertThat(validationResult).isNotNull();
    assertThat(validationResult.suggestions()).isEmpty();
    assertThat(validationResult.errors()).hasSize(1);
    assertThat(validationResult.errors().get(0).message()).contains("could not find expected ':'");
  }
}
