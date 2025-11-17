package io.github.sharma_manish_94.schemasculpt_api.service;

import static org.assertj.core.api.AssertionsForInterfaceTypes.assertThat;

import com.fasterxml.jackson.databind.ObjectMapper;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.parser.OpenAPIV3Parser;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.Map;
import java.util.Set;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

class AnalysisServiceTest {

  private AnalysisService analysisService;
  private OpenAPI openAPI;

  @BeforeEach
  void setUp() {
    analysisService = new AnalysisService(new ObjectMapper());
    String specText;
    try (InputStream inputStream = getClass().getResourceAsStream("/petStore.json")) {
      if (inputStream == null) {
        throw new IllegalArgumentException("petStore.json not found in resources");
      }
      specText = new String(inputStream.readAllBytes(), StandardCharsets.UTF_8);
    } catch (IOException e) {
      throw new RuntimeException(e);
    }
    openAPI = new OpenAPIV3Parser().readContents(specText).getOpenAPI();
  }

  @AfterEach
  void tearDown() {}

  @Test
  void buildReverseDependencyGraph_shouldCorrectlyIdentifyDependents() {
    Map<String, Set<String>> graph = analysisService.buildReverseDependencyGraph(openAPI);
    assertThat(graph).isNotNull();
  }

  //  @Test
  //  void calculateMaxDepth_shouldCorrectlyCalculateNesting() {
  //    var operation = openAPI.getPaths().get("/pet").getPost();
  //
  //    int depth = analysisService.calculateMaxDepth(openAPI, operation);
  //    assertThat(depth).isEqualTo(2);
  //  }
}
