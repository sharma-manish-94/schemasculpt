package io.github.sharmanish.schemasculpt.service.ai;

import com.fasterxml.jackson.core.JsonProcessingException;
import io.github.sharmanish.schemasculpt.dto.AIMetaAnalysisRequest;
import io.github.sharmanish.schemasculpt.dto.AIMetaAnalysisResponse;
import io.github.sharmanish.schemasculpt.dto.AIProxyRequest;
import io.github.sharmanish.schemasculpt.dto.AIResponse;
import io.github.sharmanish.schemasculpt.dto.DescriptionAnalysisRequest;
import io.github.sharmanish.schemasculpt.dto.DescriptionAnalysisResponse;
import io.github.sharmanish.schemasculpt.dto.ai.SmartAIFixRequest;
import io.github.sharmanish.schemasculpt.dto.ai.SmartAIFixResponse;
import io.github.sharmanish.schemasculpt.service.SessionService;
import io.github.sharmanish.schemasculpt.service.SpecParsingService;
import io.swagger.v3.core.util.Json;
import io.swagger.v3.core.util.Yaml;
import io.github.sharmanish.schemasculpt.exception.AIServiceException;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.Operation;
import io.swagger.v3.oas.models.PathItem;
import io.swagger.v3.oas.models.media.Schema;
import io.github.sharmanish.schemasculpt.util.VirtualThreads;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Objects;
import java.util.concurrent.ExecutorService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;

@Service
@Slf4j
public class AIService {
  private final WebClient webClient;
  private final SessionService sessionService;
  private final SpecParsingService specParsingService;
  private final ExecutorService virtualThreadExecutor;

  public AIService(
      WebClient.Builder webClientBuilder,
      @Value("${ai.service.url}") String aiServiceUrl,
      SessionService sessionService,
      SpecParsingService specParsingService,
      @Qualifier("virtualThreadExecutor") ExecutorService virtualThreadExecutor) {
    Objects.requireNonNull(webClientBuilder, "webClientBuilder must not be null");
    Objects.requireNonNull(aiServiceUrl, "aiServiceUrl must not be null");
    this.webClient = webClientBuilder.baseUrl(aiServiceUrl).build();
    this.sessionService = Objects.requireNonNull(sessionService, "sessionService must not be null");
    this.specParsingService =
        Objects.requireNonNull(specParsingService, "specParsingService must not be null");
    this.virtualThreadExecutor =
        Objects.requireNonNull(virtualThreadExecutor, "virtualThreadExecutor must not be null");
  }

  public String processSpecification(String sessionId, String userPrompt) {
    log.info("Processing AI request for sessionId: {}", sessionId);
    OpenAPI openApi = sessionService.getSpecForSession(sessionId);
    String specText = Json.pretty(openApi);

    // Use smart fix endpoint for optimized processing
    SmartAIFixRequest smartRequest = new SmartAIFixRequest(specText, userPrompt);
    String updatedSpecText = callSmartAIFix(smartRequest);

    OpenAPI updatedOpenApi = specParsingService.parse(updatedSpecText).getOpenAPI();
    sessionService.updateSessionSpec(sessionId, updatedOpenApi);
    return updatedSpecText;
  }

  /**
   * Call the optimized smart AI fix endpoint. This endpoint intelligently chooses between JSON
   * patches (fast, targeted) and full regeneration (slow, broad changes) based on the prompt.
   */
  private String callSmartAIFix(SmartAIFixRequest request) {
    log.info("Calling smart AI fix endpoint");

    try {
      SmartAIFixResponse response =
          VirtualThreads.executeBlocking(
              virtualThreadExecutor,
              () ->
                  this.webClient
                      .post()
                      .uri("/ai/fix/smart")
                      .contentType(MediaType.APPLICATION_JSON)
                      .bodyValue(request)
                      .retrieve()
                      .bodyToMono(SmartAIFixResponse.class)
                      .block());

      if (response != null && response.updatedSpecText() != null) {
        log.info(
            "Smart AI fix completed using {} method in {}ms ({} tokens)",
            response.methodUsed(),
            response.processingTimeMs(),
            response.tokenCount());
        return formatSpec(response.updatedSpecText());
      } else {
        log.warn("Smart AI fix returned null or empty response, response: {}", response);
        throw new AIServiceException("AI service returned invalid response");
      }
    } catch (Exception e) {
      log.error("Smart AI fix failed, falling back to legacy endpoint: {}", e.getMessage());
      // Fallback to legacy endpoint if smart fix fails
      AIProxyRequest legacyRequest = new AIProxyRequest(request.specText(), request.prompt());
      return callAIService(legacyRequest);
    }
  }

  private String formatSpec(String rawSpec) {
    if (rawSpec == null || rawSpec.isBlank()) {
      return "";
    }
    try {
      // Heuristic to detect if the string is JSON
      if (rawSpec.trim().startsWith("{")) {
        Object jsonObject = Json.mapper().readValue(rawSpec, Object.class);
        return Json.pretty(jsonObject);
      } else {
        Object yamlObject = Yaml.mapper().readValue(rawSpec, Object.class);
        return Yaml.pretty(yamlObject);
      }
    } catch (JsonProcessingException e) {
      return rawSpec;
    }
  }

  /**
   * Legacy method: Call the original /process endpoint for full regeneration. Kept for backward
   * compatibility, but prefer callSmartAIFix() for better performance.
   */
  @Deprecated
  private String callAIService(AIProxyRequest aiRequest) {
    return VirtualThreads.executeBlocking(
        virtualThreadExecutor,
        () ->
            this.webClient
                .post()
                .uri("/process")
                .contentType(MediaType.APPLICATION_JSON)
                .bodyValue(aiRequest)
                .retrieve()
                .bodyToMono(AIResponse.class)
                .map(AIResponse::updatedSpecText)
                .map(this::formatSpec)
                .block());
  }

  public String processSpecification(OpenAPI openApi, String userPrompt) {
    String specText = Json.pretty(openApi);
    AIProxyRequest aiRequest = new AIProxyRequest(specText, userPrompt);
    return callAIService(aiRequest);
  }

  public Map<String, Object> explainValidationIssue(Map<String, Object> request) {
    log.info("Requesting explanation for validation issue");

    try {
      return VirtualThreads.executeBlocking(
          virtualThreadExecutor,
          () ->
              this.webClient
                  .post()
                  .uri("/ai/explain")
                  .contentType(MediaType.APPLICATION_JSON)
                  .bodyValue(request)
                  .retrieve()
                  .bodyToMono(new ParameterizedTypeReference<Map<String, Object>>() {})
                  .block());
    } catch (Exception e) {
      log.error("Failed to get explanation from AI service: {}", e.getMessage(), e);
      throw new AIServiceException("AI explanation service unavailable", e);
    }
  }

  public Map<String, Object> generateTestCases(Map<String, Object> request) {
    log.info("Requesting test case generation for operation: {}", request.get("operation_summary"));

    try {
      return VirtualThreads.executeBlocking(
          virtualThreadExecutor,
          () ->
              this.webClient
                  .post()
                  .uri("/ai/test-cases/generate")
                  .contentType(MediaType.APPLICATION_JSON)
                  .bodyValue(request)
                  .retrieve()
                  .bodyToMono(new ParameterizedTypeReference<Map<String, Object>>() {})
                  .block());
    } catch (Exception e) {
      log.error("Failed to generate test cases from AI service: {}", e.getMessage(), e);
      throw new AIServiceException("AI test generation service unavailable", e);
    }
  }

  public Map<String, Object> generateTestSuite(Map<String, Object> request) {
    log.info("Requesting complete test suite generation");

    try {
      return VirtualThreads.executeBlocking(
          virtualThreadExecutor,
          () ->
              this.webClient
                  .post()
                  .uri("/ai/test-suite/generate")
                  .contentType(MediaType.APPLICATION_JSON)
                  .bodyValue(request)
                  .retrieve()
                  .bodyToMono(new ParameterizedTypeReference<Map<String, Object>>() {})
                  .block());
    } catch (Exception e) {
      log.error("Failed to generate test suite from AI service: {}", e.getMessage(), e);
      throw new AIServiceException("AI test suite generation service unavailable", e);
    }
  }

  /**
   * Perform AI meta-analysis on linter findings to detect higher-order patterns, security threats,
   * and design issues.
   */
  public AIMetaAnalysisResponse performMetaAnalysis(AIMetaAnalysisRequest request) {
    log.info(
        "Requesting AI meta-analysis with {} errors and {} suggestions",
        request.errors().size(),
        request.suggestions().size());

    try {
      AIMetaAnalysisResponse response =
          VirtualThreads.executeBlocking(
              virtualThreadExecutor,
              () ->
                  this.webClient
                      .post()
                      .uri("/ai/meta-analysis")
                      .contentType(MediaType.APPLICATION_JSON)
                      .bodyValue(request)
                      .retrieve()
                      .bodyToMono(AIMetaAnalysisResponse.class)
                      .block());

      if (response != null) {
        log.info(
            "Meta-analysis completed with {} insights (confidence: {})",
            response.insights().size(),
            response.confidenceScore());
        return response;
      } else {
        log.warn("Meta-analysis returned null response");
        throw new AIServiceException("AI meta-analysis service returned invalid response");
      }
    } catch (Exception e) {
      log.error("Failed to perform AI meta-analysis: {}", e.getMessage(), e);
      throw new AIServiceException("AI meta-analysis service unavailable", e);
    }
  }

  /**
   * Extract descriptions from OpenAPI spec with minimal context. This method DOES NOT send the
   * entire spec to AI, only descriptions and necessary context.
   */
  public DescriptionAnalysisRequest extractDescriptionsForAnalysis(OpenAPI openAPI) {
    List<DescriptionAnalysisRequest.DescriptionItem> items = new ArrayList<>();

    // Extract operation descriptions
    if (openAPI.getPaths() != null) {
      openAPI
          .getPaths()
          .forEach(
              (path, pathItem) -> {
                extractOperationDescriptions(path, pathItem, items);
              });
    }

    // Extract schema descriptions
    if (openAPI.getComponents() != null && openAPI.getComponents().getSchemas() != null) {
      openAPI
          .getComponents()
          .getSchemas()
          .forEach(
              (schemaName, schema) -> {
                extractSchemaDescription(schemaName, schema, items);
              });
    }

    log.info("Extracted {} descriptions for quality analysis", items.size());
    return new DescriptionAnalysisRequest(items);
  }

  private void extractOperationDescriptions(
      String path, PathItem pathItem, List<DescriptionAnalysisRequest.DescriptionItem> items) {
    // Build map with only non-null operations (Map.of() doesn't accept null values)
    Map<String, Operation> operations = new java.util.HashMap<>();
    if (pathItem.getGet() != null) {
      operations.put("get", pathItem.getGet());
    }
    if (pathItem.getPost() != null) {
      operations.put("post", pathItem.getPost());
    }
    if (pathItem.getPut() != null) {
      operations.put("put", pathItem.getPut());
    }
    if (pathItem.getDelete() != null) {
      operations.put("delete", pathItem.getDelete());
    }
    if (pathItem.getPatch() != null) {
      operations.put("patch", pathItem.getPatch());
    }

    operations.forEach(
        (method, operation) -> {
          String jsonPath = "/paths/" + path.replace("/", "~1") + "/" + method;
          DescriptionAnalysisRequest.DescriptionContext context =
              new DescriptionAnalysisRequest.DescriptionContext(
                  method.toUpperCase(Locale.ROOT), null, null, operation.getSummary(), null);

          items.add(
              new DescriptionAnalysisRequest.DescriptionItem(
                  jsonPath + "/description", "operation", operation.getDescription(), context));
        });
  }

  private void extractSchemaDescription(
      String schemaName, Schema schema, List<DescriptionAnalysisRequest.DescriptionItem> items) {
    String jsonPath = "/components/schemas/" + schemaName;

    List<String> propertyNames = null;
    if (schema.getProperties() != null) {
      propertyNames = new ArrayList<>(schema.getProperties().keySet());
    }

    DescriptionAnalysisRequest.DescriptionContext context =
        new DescriptionAnalysisRequest.DescriptionContext(
            null, schema.getType(), propertyNames, null, null);

    items.add(
        new DescriptionAnalysisRequest.DescriptionItem(
            jsonPath + "/description", "schema", schema.getDescription(), context));
  }

  /**
   * Analyze description quality using AI service. Returns quality scores, issues, and JSON Patch
   * operations for improvements.
   */
  public DescriptionAnalysisResponse analyzeDescriptionQuality(DescriptionAnalysisRequest request) {
    log.info("Requesting description quality analysis for {} items", request.items().size());

    try {
      DescriptionAnalysisResponse response =
          VirtualThreads.executeBlocking(
              virtualThreadExecutor,
              () ->
                  this.webClient
                      .post()
                      .uri("/ai/analyze-descriptions")
                      .contentType(MediaType.APPLICATION_JSON)
                      .bodyValue(request)
                      .retrieve()
                      .bodyToMono(DescriptionAnalysisResponse.class)
                      .block());

      if (response != null) {
        log.info(
            "Description analysis completed with overall score: {} ({} patches" + " generated)",
            response.overallScore(),
            response.patches().size());
        return response;
      } else {
        log.warn("Description analysis returned null response");
        throw new AIServiceException("AI description analysis service returned invalid response");
      }
    } catch (Exception e) {
      log.error("Failed to analyze description quality: {}", e.getMessage(), e);
      throw new AIServiceException("AI description analysis service unavailable", e);
    }
  }
}
