package io.github.sharma_manish_94.schemasculpt_api.controller;

import io.github.sharma_manish_94.schemasculpt_api.service.AnalysisService;
import io.github.sharma_manish_94.schemasculpt_api.service.SessionService;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.Operation;
import io.swagger.v3.oas.models.PathItem;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;
import java.util.Set;

@RestController
@RequestMapping("/api/v1/sessions/{sessionId}/analysis")
public class AnalysisController {

    private final SessionService sessionService;
    private final AnalysisService analysisService;

    public AnalysisController(SessionService sessionService, AnalysisService analysisService) {
        this.sessionService = sessionService;
        this.analysisService = analysisService;
    }

    @GetMapping("/dependencies")
    public ResponseEntity<Map<String, Set<String>>> getDependencyGraph(@PathVariable String sessionId) {
        OpenAPI openApi = sessionService.getSpecForSession(sessionId);
        if (openApi == null) {
            return ResponseEntity.notFound().build();
        }
        Map<String, Set<String>> graph = analysisService.buildReverseDependencyGraph(openApi);
        return ResponseEntity.ok(graph);
    }

    @GetMapping("/nesting-depth")
    public ResponseEntity<Integer> getNestingDepth(
            @PathVariable String sessionId,
            @RequestParam String path,
            @RequestParam String method) {

        OpenAPI openApi = sessionService.getSpecForSession(sessionId);
        if (openApi == null || openApi.getPaths() == null) {
            return ResponseEntity.notFound().build();
        }

        PathItem pathItem = openApi.getPaths().get(path);
        if (pathItem == null) {
            return ResponseEntity.notFound().build();
        }

        Operation operation = pathItem.readOperationsMap().get(PathItem.HttpMethod.valueOf(method.toUpperCase()));
        if (operation == null) {
            return ResponseEntity.notFound().build();
        }

        int depth = analysisService.calculateMaxDepth(openApi, operation);
        return ResponseEntity.ok(depth);
    }
}
