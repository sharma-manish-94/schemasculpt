package io.github.sharmanish.schemasculpt.service;

import io.github.sharmanish.schemasculpt.dto.diff.DiffResult;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;

import static org.junit.jupiter.api.Assertions.assertNotNull;

@ExtendWith(MockitoExtension.class)
class SchemaDiffServiceTest {

  private SchemaDiffService schemaDiffService;

  @Mock
  private TreeDistanceService treeDistanceService;

  @BeforeEach
  void setUp() {
    schemaDiffService = new SchemaDiffService(treeDistanceService);
  }
  @Test
  void compareSpecs() {
    String specText1;
    try (InputStream inputStream = getClass().getResourceAsStream("/old-spec.yaml")) {
      if (inputStream == null) {
        throw new IllegalArgumentException("old-spec.yaml not found in resources");
      }
      specText1 = new String(inputStream.readAllBytes(), StandardCharsets.UTF_8);
    } catch (IOException e) {
      throw new RuntimeException(e);
    }
    String specText2;
    try (InputStream inputStream = getClass().getResourceAsStream("/new-spec.yaml")) {
      if (inputStream == null) {
        throw new IllegalArgumentException("new-spec.yaml not found in resources");
      }
      specText2 = new String(inputStream.readAllBytes(), StandardCharsets.UTF_8);
    } catch (IOException e) {
      throw new RuntimeException(e);
    }
    DiffResult diffResult = schemaDiffService.compareSpecs(specText1, specText2);
    assertNotNull(diffResult);

  }
}
