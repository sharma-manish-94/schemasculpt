package io.github.sharma_manish_94.schemasculpt_api.controller;

import io.github.sharma_manish_94.schemasculpt_api.service.AnalysisService;
import io.github.sharma_manish_94.schemasculpt_api.service.SessionService;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.Operation;
import io.swagger.v3.oas.models.PathItem;
import java.util.Map;
import java.util.Set;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

@RestController
@RequestMapping("/api/v1/sessions/{sessionId}/analysis")
public class AnalysisController {

  private final SessionService sessionService;
  private final AnalysisService analysisService;
  private final WebClient webClient;

  public AnalysisController(
      SessionService sessionService,
      AnalysisService analysisService,
      WebClient.Builder webClientBuilder,
      @Value("${ai.service.url}") String aiServiceUrl) {
    this.sessionService = sessionService;
    this.analysisService = analysisService;
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
        pathItem.readOperationsMap().get(PathItem.HttpMethod.valueOf(method.toUpperCase()));
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
        .bodyToMono(new org.springframework.core.ParameterizedTypeReference<Map<String, Object>>() {})
        .timeout(java.time.Duration.ofMinutes(5))  // 5 minute timeout for complex analysis
        .map(ResponseEntity::ok)
        .onErrorResume(
            error ->
                Mono.just(
                    ResponseEntity.status(500)
                        .body(Map.of("error", "Attack path simulation failed", "message", error.getMessage()))));
  }
}
