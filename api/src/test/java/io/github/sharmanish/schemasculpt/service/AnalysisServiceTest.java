package io.github.sharmanish.schemasculpt.service;

import static org.assertj.core.api.AssertionsForInterfaceTypes.assertThat;

import io.github.sharmanish.schemasculpt.dto.analysis.AuthzMatrixResponse;
import io.github.sharmanish.schemasculpt.dto.analysis.SchemaSimilarityResponse;
import io.github.sharmanish.schemasculpt.dto.analysis.TaintAnalysisResponse;
import io.github.sharmanish.schemasculpt.dto.analysis.ZombieApiResponse;
import io.github.sharmanish.schemasculpt.service.analyzer.complexity.NestingDepthAnalyzer;
import io.github.sharmanish.schemasculpt.service.analyzer.dependency.BlastRadiusAnalyzer;
import io.github.sharmanish.schemasculpt.service.analyzer.dependency.ReverseDependencyGraphAnalyzer;
import io.github.sharmanish.schemasculpt.service.analyzer.quality.SchemaSimilarityAnalyzer;
import io.github.sharmanish.schemasculpt.service.analyzer.quality.ZombieApiAnalyzer;
import io.github.sharmanish.schemasculpt.service.analyzer.security.AuthorizationMatrixAnalyzer;
import io.github.sharmanish.schemasculpt.service.analyzer.security.TaintAnalyzer;
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
import tools.jackson.databind.json.JsonMapper;

class AnalysisServiceTest {

  private AnalysisService analysisService;
  private OpenAPI openAPI;

  @BeforeEach
  void setUp() {
    // Create all analyzers
    JsonMapper jsonMapper = new JsonMapper();
    ReverseDependencyGraphAnalyzer dependencyGraphAnalyzer = new ReverseDependencyGraphAnalyzer();
    BlastRadiusAnalyzer blastRadiusAnalyzer = new BlastRadiusAnalyzer(dependencyGraphAnalyzer);
    NestingDepthAnalyzer nestingDepthAnalyzer = new NestingDepthAnalyzer(jsonMapper);
    TaintAnalyzer taintAnalyzer = new TaintAnalyzer();
    AuthorizationMatrixAnalyzer authzMatrixAnalyzer = new AuthorizationMatrixAnalyzer();
    SchemaSimilarityAnalyzer schemaSimilarityAnalyzer = new SchemaSimilarityAnalyzer();
    ZombieApiAnalyzer zombieApiAnalyzer = new ZombieApiAnalyzer();

    // Create AnalysisService with all analyzers
    analysisService =
        new AnalysisService(
            dependencyGraphAnalyzer,
            blastRadiusAnalyzer,
            nestingDepthAnalyzer,
            taintAnalyzer,
            authzMatrixAnalyzer,
            schemaSimilarityAnalyzer,
            zombieApiAnalyzer);
  }

  @AfterEach
  void tearDown() {}

  @Test
  void buildReverseDependencyGraph_shouldCorrectlyIdentifyDependents() {
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
    Map<String, Set<String>> graph = analysisService.buildReverseDependencyGraph(openAPI);
    assertThat(graph).isNotNull();
  }

  @Test
  void testAdvancedAnalysis_TaintPath() {
    String specText;
    try (InputStream inputStream = getClass().getResourceAsStream("/vulnerable-api.json")) {
      if (inputStream == null) {
        throw new IllegalArgumentException("vulnerable-api.json not found in resources");
      }
      specText = new String(inputStream.readAllBytes(), StandardCharsets.UTF_8);
    } catch (IOException e) {
      throw new RuntimeException(e);
    }
    openAPI = new OpenAPIV3Parser().readContents(specText).getOpenAPI();
    TaintAnalysisResponse taintAnalysisResponse = analysisService.performTaintAnalysis(openAPI);
    assertThat(taintAnalysisResponse).isNotNull();
    assertThat(taintAnalysisResponse.vulnerabilities()).hasSize(1);
  }

  @Test
  void testAdvancedAnalysis_AuthzMatrix() {
    String specText;
    try (InputStream inputStream = getClass().getResourceAsStream("/vulnerable-api.json")) {
      if (inputStream == null) {
        throw new IllegalArgumentException("vulnerable-api.json not found in resources");
      }
      specText = new String(inputStream.readAllBytes(), StandardCharsets.UTF_8);
    } catch (IOException e) {
      throw new RuntimeException(e);
    }
    openAPI = new OpenAPIV3Parser().readContents(specText).getOpenAPI();
    AuthzMatrixResponse authzMatrixResponse = analysisService.generateAuthzMatrix(openAPI);
    assertThat(authzMatrixResponse).isNotNull();
  }

  @Test
  void testAdvancedAnalysis_ZombieAPI() {
    String specText;
    try (InputStream inputStream = getClass().getResourceAsStream("/zombie-api.json")) {
      if (inputStream == null) {
        throw new IllegalArgumentException("vulnerable-api.json not found in resources");
      }
      specText = new String(inputStream.readAllBytes(), StandardCharsets.UTF_8);
    } catch (IOException e) {
      throw new RuntimeException(e);
    }
    openAPI = new OpenAPIV3Parser().readContents(specText).getOpenAPI();
    ZombieApiResponse zombieApiResponse = analysisService.detectZombieApis(openAPI);
    assertThat(zombieApiResponse).isNotNull();
  }

  @Test
  void testAdvancedAnalysis_SchemaSimilarity() {
    String specText;
    try (InputStream inputStream = getClass().getResourceAsStream("/schema-similarity.json")) {
      if (inputStream == null) {
        throw new IllegalArgumentException("vulnerable-api.json not found in resources");
      }
      specText = new String(inputStream.readAllBytes(), StandardCharsets.UTF_8);
    } catch (IOException e) {
      throw new RuntimeException(e);
    }
    openAPI = new OpenAPIV3Parser().readContents(specText).getOpenAPI();
    SchemaSimilarityResponse schemaSimilarityResponse =
        analysisService.analyzeSchemaSimilarity(openAPI);
    assertThat(schemaSimilarityResponse).isNotNull();
  }
}
