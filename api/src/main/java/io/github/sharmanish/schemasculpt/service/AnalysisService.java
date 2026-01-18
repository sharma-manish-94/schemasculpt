package io.github.sharmanish.schemasculpt.service;

import io.github.sharmanish.schemasculpt.dto.analysis.AuthzMatrixResponse;
import io.github.sharmanish.schemasculpt.dto.analysis.BlastRadiusResponse;
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
import io.swagger.v3.oas.models.Operation;
import io.swagger.v3.parser.OpenAPIV3Parser;
import io.swagger.v3.parser.core.models.ParseOptions;
import io.swagger.v3.parser.core.models.SwaggerParseResult;
import java.util.Map;
import java.util.Set;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

/**
 * Facade service orchestrating OpenAPI analysis operations.
 *
 * <p>Delegates to specialized analyzers following Single Responsibility Principle. Maintains full
 * backward compatibility with existing API consumers.
 *
 * <p>Each analysis operation is implemented by a dedicated analyzer:
 *
 * <ul>
 *   <li>Dependency analysis: {@link ReverseDependencyGraphAnalyzer}, {@link BlastRadiusAnalyzer}
 *   <li>Complexity analysis: {@link NestingDepthAnalyzer}
 *   <li>Security analysis: {@link TaintAnalyzer}, {@link AuthorizationMatrixAnalyzer}
 *   <li>Quality analysis: {@link SchemaSimilarityAnalyzer}, {@link ZombieApiAnalyzer}
 * </ul>
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class AnalysisService {

  private final ReverseDependencyGraphAnalyzer dependencyGraphAnalyzer;
  private final BlastRadiusAnalyzer blastRadiusAnalyzer;
  private final NestingDepthAnalyzer nestingDepthAnalyzer;
  private final TaintAnalyzer taintAnalyzer;
  private final AuthorizationMatrixAnalyzer authzMatrixAnalyzer;
  private final SchemaSimilarityAnalyzer schemaSimilarityAnalyzer;
  private final ZombieApiAnalyzer zombieApiAnalyzer;

  /**
   * Builds a map where the key is a component name and the value is a set of all other
   * components/operations that depend on it.
   *
   * @param openApi The OpenAPI specification
   * @return Reverse dependency graph
   */
  public Map<String, Set<String>> buildReverseDependencyGraph(OpenAPI openApi) {
    log.debug("Building reverse dependency graph");
    return dependencyGraphAnalyzer.analyze(openApi);
  }

  /**
   * Calculates maximum nesting depth for all operations.
   *
   * @param specText The OpenAPI specification as text
   * @return Map of operation key to maximum nesting depth
   */
  public Map<String, Integer> calculateAllDepths(String specText) {
    log.debug("Calculating nesting depths from spec text");
    OpenAPI openApi = parseOpenApiSpec(specText);
    return nestingDepthAnalyzer.analyze(openApi);
  }

  /**
   * Calculates maximum nesting depth for all operations.
   *
   * @param openApi The OpenAPI specification
   * @return Map of operation key to maximum nesting depth
   */
  public Map<String, Integer> calculateAllDepths(final OpenAPI openApi) {
    log.debug("Calculating nesting depths from OpenAPI object");
    return nestingDepthAnalyzer.analyze(openApi);
  }

  /**
   * Calculates nesting depth for a specific operation.
   *
   * @param operation The operation to analyze
   * @param openApi The OpenAPI specification
   * @return The maximum nesting depth
   */
  public int calculateNestingDepthForOperation(Operation operation, OpenAPI openApi) {
    log.debug("Calculating nesting depth for single operation");
    return nestingDepthAnalyzer.analyzeOperation(operation, openApi);
  }

  /**
   * Generates an authorization matrix showing required scopes for each operation.
   *
   * @param openApi The OpenAPI specification
   * @return Authorization matrix response
   */
  public AuthzMatrixResponse generateAuthzMatrix(OpenAPI openApi) {
    log.debug("Generating authorization matrix");
    return authzMatrixAnalyzer.analyze(openApi);
  }

  /**
   * Performs taint analysis to detect sensitive data leakage.
   *
   * @param openApi The OpenAPI specification
   * @return Taint analysis response with vulnerabilities
   */
  public TaintAnalysisResponse performTaintAnalysis(OpenAPI openApi) {
    log.debug("Performing taint analysis");
    return taintAnalyzer.analyze(openApi);
  }

  /**
   * Analyzes schema similarity using Jaccard index.
   *
   * @param openApi The OpenAPI specification
   * @return Schema similarity response with clusters
   */
  public SchemaSimilarityResponse analyzeSchemaSimilarity(OpenAPI openApi) {
    log.debug("Analyzing schema similarity");
    return schemaSimilarityAnalyzer.analyze(openApi);
  }

  /**
   * Detects zombie APIs (shadowed paths and orphaned operations).
   *
   * @param openApi The OpenAPI specification
   * @return Zombie API detection response
   */
  public ZombieApiResponse detectZombieApis(OpenAPI openApi) {
    log.debug("Detecting zombie APIs");
    return zombieApiAnalyzer.analyze(openApi);
  }

  /**
   * Performs blast radius analysis for a target schema.
   *
   * @param specContent The OpenAPI specification content
   * @param targetSchema The target schema name
   * @return Blast radius analysis response
   */
  public BlastRadiusResponse performBlastRadiusAnalysis(String specContent, String targetSchema) {
    log.debug("Performing blast radius analysis for schema: {}", targetSchema);
    OpenAPI openApi = parseOpenApiSpec(specContent);
    return blastRadiusAnalyzer.analyze(openApi, targetSchema);
  }

  /**
   * Parses OpenAPI specification from text.
   *
   * @param specText The specification text
   * @return Parsed OpenAPI object
   */
  private OpenAPI parseOpenApiSpec(String specText) {
    ParseOptions options = new ParseOptions();
    options.setResolve(false);

    SwaggerParseResult parseResult = new OpenAPIV3Parser().readContents(specText, null, options);

    if (parseResult.getMessages() != null && !parseResult.getMessages().isEmpty()) {
      log.warn("Warnings during OpenAPI parsing: {}", parseResult.getMessages());
    }

    return parseResult.getOpenAPI();
  }
}
