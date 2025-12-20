package io.github.sharmanish.schemasculpt.controller;

import io.github.sharmanish.schemasculpt.dto.analysis.AuthzMatrixResponse;
import io.github.sharmanish.schemasculpt.dto.analysis.BlastRadiusResponse;
import io.github.sharmanish.schemasculpt.dto.analysis.SchemaSimilarityResponse;
import io.github.sharmanish.schemasculpt.dto.analysis.SecurityFinding;
import io.github.sharmanish.schemasculpt.dto.analysis.SecurityFindingsRequest;
import io.github.sharmanish.schemasculpt.dto.analysis.TaintAnalysisResponse;
import io.github.sharmanish.schemasculpt.dto.analysis.ZombieApiResponse;
import io.github.sharmanish.schemasculpt.service.AnalysisService;
import io.github.sharmanish.schemasculpt.service.SecurityFindingsExtractor;
import io.github.sharmanish.schemasculpt.service.SessionService;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.Operation;
import io.swagger.v3.oas.models.PathItem;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

import java.util.Locale;
import java.util.Map;
import java.util.Set;

@RestController
@RequestMapping("/api/v1/sessions/{sessionId}/analysis")
public class AnalysisController {

  private final SessionService sessionService;
  private final AnalysisService analysisService;
  private final SecurityFindingsExtractor securityFindingsExtractor;
  private final WebClient webClient;

  public AnalysisController(
      SessionService sessionService,
      AnalysisService analysisService,
      SecurityFindingsExtractor securityFindingsExtractor,
      WebClient.Builder webClientBuilder,
      @Value("${ai.service.url}") String aiServiceUrl) {
    this.sessionService = sessionService;
    this.analysisService = analysisService;
    this.securityFindingsExtractor = securityFindingsExtractor;
    this.webClient = webClientBuilder.baseUrl(aiServiceUrl).build();
  }

  @GetMapping("/dependencies")
  public ResponseEntity<Map<String, Set<String>>> getDependencyGraph(
      @PathVariable String sessionId) {
    OpenAPI openApi = sessionService.getSpecForSession(sessionId);
    if (openApi == null) {
      return ResponseEntity.notFound().build();
    }
    Map<String, Set<String>> graph = analysisService.buildReverseDependencyGraph(openApi);
    return ResponseEntity.ok(graph);
  }

  @GetMapping("/nesting-depth")
  public ResponseEntity<Map<String, Integer>> getNestingDepth(
      @PathVariable String sessionId, @RequestParam String path, @RequestParam String method) {

    OpenAPI openApi = sessionService.getSpecForSession(sessionId);
    if (openApi == null || openApi.getPaths() == null) {
      return ResponseEntity.notFound().build();
    }

    PathItem pathItem = openApi.getPaths().get(path);
    if (pathItem == null) {
      return ResponseEntity.notFound().build();
    }

    Operation operation =
        pathItem.readOperationsMap().get(PathItem.HttpMethod.valueOf(method.toUpperCase(Locale.ROOT)));
    if (operation == null) {
      return ResponseEntity.notFound().build();
    }

    int depth = analysisService.calculateNestingDepthForOperation(operation, openApi);
    return ResponseEntity.ok(Map.of("depth", depth));
  }

  @PostMapping("/attack-path-simulation")
  public Mono<ResponseEntity<Map<String, Object>>> runAttackPathSimulation(
      @PathVariable String sessionId,
      @RequestParam(defaultValue = "standard") String analysisDepth,
      @RequestParam(defaultValue = "5") int maxChainLength,
      @RequestParam(defaultValue = "false") boolean excludeLowSeverity) {

    String specText = sessionService.getSpecTextForSession(sessionId);
    if (specText == null) {
      return Mono.just(ResponseEntity.notFound().build());
    }

    Map<String, Object> requestBody =
        Map.of(
            "spec_text", specText,
            "analysis_depth", analysisDepth,
            "max_chain_length", maxChainLength,
            "exclude_low_severity", excludeLowSeverity);

    return webClient
        .post()
        .uri("/ai/security/attack-path-simulation")
        .bodyValue(requestBody)
        .retrieve()
        .bodyToMono(new org.springframework.core.ParameterizedTypeReference<Map<String, Object>>() {
        })
        .timeout(java.time.Duration.ofMinutes(5))  // 5 minute timeout for complex analysis
        .map(ResponseEntity::ok)
        .onErrorResume(
            error -> {
              String errorMessage = error.getMessage() != null ? error.getMessage() :
                  error.getClass().getSimpleName();
              return Mono.just(
                  ResponseEntity.status(500)
                      .body(Map.of("error", "Attack path simulation failed", "message",
                          errorMessage)));
            });
  }

  @PostMapping("/attack-path-findings")
  public Mono<ResponseEntity<Map<String, Object>>> runAttackPathAnalysisFromFindings(
      @PathVariable String sessionId,
      @RequestParam(defaultValue = "standard") String analysisDepth,
      @RequestParam(defaultValue = "5") int maxChainLength,
      @RequestParam(defaultValue = "false") boolean excludeLowSeverity) {

    OpenAPI openApi = sessionService.getSpecForSession(sessionId);
    if (openApi == null) {
      return Mono.just(ResponseEntity.notFound().build());
    }

    // Step 1: Extract FACTUAL security findings using deterministic Java analysis
    // This is FAST and 100% ACCURATE - no AI guessing
    java.util.List<SecurityFinding> findings = securityFindingsExtractor.extractFindings(openApi);

    // Step 2: Build request with findings (NOT the full spec)
    // This payload is tiny compared to sending the entire 5MB spec!
    SecurityFindingsRequest request = new SecurityFindingsRequest(
        findings,
        analysisDepth,
        maxChainLength,
        excludeLowSeverity
    );

    // Step 3: Send findings to AI for REASONING about attack chains
    // AI does what it's best at: Finding patterns and reasoning about security implications
    return webClient
        .post()
        .uri("/ai/security/attack-path-findings")
        .bodyValue(request)
        .retrieve()
        .bodyToMono(new org.springframework.core.ParameterizedTypeReference<Map<String, Object>>() {
        })
        .timeout(java.time.Duration.ofMinutes(2))  // Much faster than spec-based approach!
        .map(ResponseEntity::ok)
        .onErrorResume(
            error -> {
              String errorMessage = error.getMessage() != null ? error.getMessage() :
                  error.getClass().getSimpleName();
              return Mono.just(
                  ResponseEntity.status(500)
                      .body(Map.of(
                          "error", "Attack path analysis from findings failed",
                          "message", errorMessage,
                          "findings_count", findings.size())));
            });
  }

  @GetMapping("/authz-matrix")
  public ResponseEntity<AuthzMatrixResponse> getAuthzMatrix(@PathVariable String sessionId) {
    OpenAPI openApi = sessionService.getSpecForSession(sessionId);
    if (openApi == null) {
      return ResponseEntity.notFound().build();
    }
    AuthzMatrixResponse response = analysisService.generateAuthzMatrix(openApi);
    return ResponseEntity.ok(response);
  }

  @GetMapping("/taint-analysis")
  public ResponseEntity<TaintAnalysisResponse> getTaintAnalysis(@PathVariable String sessionId) {
    OpenAPI openApi = sessionService.getSpecForSession(sessionId);
    if (openApi == null) {
      return ResponseEntity.notFound().build();
    }
    TaintAnalysisResponse response = analysisService.performTaintAnalysis(openApi);
    return ResponseEntity.ok(response);
  }

  @GetMapping("/schema-similarity")
  public ResponseEntity<SchemaSimilarityResponse> getSchemaSimilarity(
      @PathVariable String sessionId) {
    OpenAPI openApi = sessionService.getSpecForSession(sessionId);
    if (openApi == null) {
      return ResponseEntity.notFound().build();
    }
    return ResponseEntity.ok(analysisService.analyzeSchemaSimilarity(openApi));
  }

  @GetMapping("/zombie-apis")
  public ResponseEntity<ZombieApiResponse> getZombieApis(@PathVariable String sessionId) {
    OpenAPI openApi = sessionService.getSpecForSession(sessionId);
    if (openApi == null) {
      return ResponseEntity.notFound().build();
    }
    return ResponseEntity.ok(analysisService.detectZombieApis(openApi));
  }

  @PostMapping("/blast-radius")
  public ResponseEntity<BlastRadiusResponse> analyzeBlastRadius(
      @RequestParam("schemaName") String schemaName,
      @RequestBody String apiSpec) {

    BlastRadiusResponse response = analysisService.performBlastRadiusAnalysis(apiSpec, schemaName);
    return ResponseEntity.ok(response);
  }
}
