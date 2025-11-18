package io.github.sharma_manish_94.schemasculpt_api.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import io.github.sharma_manish_94.schemasculpt_api.dto.analysis.AuthzMatrixResponse;
import io.github.sharma_manish_94.schemasculpt_api.dto.analysis.SchemaSimilarityResponse;
import io.github.sharma_manish_94.schemasculpt_api.dto.analysis.TaintAnalysisResponse;
import io.github.sharma_manish_94.schemasculpt_api.dto.analysis.ZombieApiResponse;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.parser.OpenAPIV3Parser;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.Map;
import java.util.Set;

import static org.assertj.core.api.AssertionsForInterfaceTypes.assertThat;

class AnalysisServiceTest {

    private AnalysisService analysisService;
    private OpenAPI openAPI;

    @BeforeEach
    void setUp() {
        analysisService = new AnalysisService(new ObjectMapper());

    }

    @AfterEach
    void tearDown() {
    }

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
        SchemaSimilarityResponse schemaSimilarityResponse = analysisService.analyzeSchemaSimilarity(openAPI);
        assertThat(schemaSimilarityResponse).isNotNull();
    }


}
