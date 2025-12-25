package io.github.sharmanish.schemasculpt.service.analyzer.security;

import io.github.sharmanish.schemasculpt.dto.analysis.TaintAnalysisResponse;
import io.github.sharmanish.schemasculpt.service.analyzer.base.AbstractSchemaAnalyzer;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.Operation;
import io.swagger.v3.oas.models.media.Schema;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import org.springframework.stereotype.Component;

/**
 * Analyzer that performs taint analysis to detect sensitive data leakage.
 *
 * <p>Tracks data flow from sensitive sources (schemas with PII/secrets) through endpoints to
 * identify potential data exposure vulnerabilities.
 *
 * <p>Severity levels:
 *
 * <ul>
 *   <li>CRITICAL: Public endpoint returning sensitive data (data leakage)
 *   <li>WARNING: Secured endpoint returning sensitive data (verify necessity)
 * </ul>
 */
@Component
public class TaintAnalyzer extends AbstractSchemaAnalyzer<TaintAnalysisResponse> {

  @Override
  protected TaintAnalysisResponse performAnalysis(OpenAPI openApi) {
    List<TaintAnalysisResponse.TaintVulnerability> vulnerabilities = new ArrayList<>();

    // Step A: Identify Sources (Schemas that contain sensitive data)
    Set<String> sensitiveSchemas = identifySensitiveSchemas(openApi);

    if (openApi.getPaths() != null) {
      openApi
          .getPaths()
          .forEach(
              (path, pathItem) -> {
                pathItem
                    .readOperationsMap()
                    .forEach(
                        (method, operation) -> {
                          // Step B: Check Barriers (Is the endpoint
                          // secured?)
                          boolean isSecured = isOperationSecured(operation, openApi);

                          // Step C: Check Sinks (Responses)
                          if (operation.getResponses() != null) {
                            operation
                                .getResponses()
                                .forEach(
                                    (statusCode, response) -> {
                                      if (response.getContent() != null) {
                                        response
                                            .getContent()
                                            .forEach(
                                                (mediaType, content) -> {
                                                  Schema<?> schema = content.getSchema();
                                                  if (schema != null) {
                                                    // Traversal: Check if response flows from a
                                                    // sensitive source
                                                    List<String> leakTrail =
                                                        findSensitiveLeak(
                                                            schema,
                                                            sensitiveSchemas,
                                                            openApi,
                                                            new HashSet<>());

                                                    if (!leakTrail.isEmpty()) {
                                                      String trailString =
                                                          String.join(" -> ", leakTrail);

                                                      if (!isSecured) {
                                                        // CRITICAL: Sensitive data on public
                                                        // endpoint
                                                        vulnerabilities.add(
                                                            new TaintAnalysisResponse
                                                                .TaintVulnerability(
                                                                method.name() + " " + path,
                                                                "CRITICAL",
                                                                "Public"
                                                                    + " endpoint"
                                                                    + " returning"
                                                                    + " sensitive"
                                                                    + " data"
                                                                    + " (Data"
                                                                    + " Leakage)",
                                                                trailString));
                                                      } else {
                                                        // WARNING: Sensitive data returned,
                                                        // verified
                                                        // security needed
                                                        vulnerabilities.add(
                                                            new TaintAnalysisResponse
                                                                .TaintVulnerability(
                                                                method.name() + " " + path,
                                                                "WARNING",
                                                                "Sensitive"
                                                                    + " data"
                                                                    + " exposure"
                                                                    + " (Verify"
                                                                    + " necessity)",
                                                                trailString));
                                                      }
                                                    }
                                                  }
                                                });
                                      }
                                    });
                          }
                        });
              });
    }
    return new TaintAnalysisResponse(vulnerabilities);
  }

  /**
   * Checks if an operation has security requirements.
   *
   * @param operation The operation to check
   * @param openApi The OpenAPI specification
   * @return true if secured, false otherwise
   */
  private boolean isOperationSecured(Operation operation, OpenAPI openApi) {
    if (operation.getSecurity() != null && !operation.getSecurity().isEmpty()) {
      return true;
    }
    // If no operation security, check global security
    return openApi.getSecurity() != null && !openApi.getSecurity().isEmpty();
  }

  /**
   * Identifies schemas that contain sensitive data.
   *
   * @param openApi The OpenAPI specification
   * @return Set of sensitive schema names
   */
  private Set<String> identifySensitiveSchemas(OpenAPI openApi) {
    Set<String> sensitiveSchemas = new HashSet<>();
    if (openApi.getComponents() == null || openApi.getComponents().getSchemas() == null) {
      return sensitiveSchemas;
    }

    openApi
        .getComponents()
        .getSchemas()
        .forEach(
            (name, schema) -> {
              // 1. Check Schema Name (e.g., "CreditCard")
              if (isSensitiveWord(name)) {
                sensitiveSchemas.add(name);
              }
              // 2. Check Properties (e.g., "password")
              else if (schema.getProperties() != null) {
                boolean hasSensitiveProp =
                    schema.getProperties().keySet().stream()
                        .anyMatch(key -> isSensitiveWord((String) key));
                if (hasSensitiveProp) {
                  sensitiveSchemas.add(name);
                }
              }
            });
    return sensitiveSchemas;
  }

  /**
   * Checks if a word contains sensitive keywords.
   *
   * @param text The text to check
   * @return true if sensitive, false otherwise
   */
  private boolean isSensitiveWord(String text) {
    if (text == null) {
      return false;
    }
    String lower = text.toLowerCase(Locale.ROOT);
    return SENSITIVE_KEYWORDS.stream().anyMatch(lower::contains);
  }

  /**
   * Recursively finds sensitive data leaks in a schema.
   *
   * @param schema The schema to analyze
   * @param sensitiveSchemas Set of sensitive schema names
   * @param openApi The OpenAPI specification
   * @param visited Set of visited schema names to prevent cycles
   * @return List of leak trail components, or empty if no leak
   */
  private List<String> findSensitiveLeak(
      Schema<?> schema, Set<String> sensitiveSchemas, OpenAPI openApi, Set<String> visited) {
    if (schema == null) {
      return Collections.emptyList();
    }

    // 1. Check $ref
    if (schema.get$ref() != null) {
      String schemaName = schema.get$ref().substring(schema.get$ref().lastIndexOf('/') + 1);

      if (visited.contains(schemaName)) {
        return Collections.emptyList(); // Cycle detected
      }

      // If this schema is marked sensitive, we found a leak!
      if (sensitiveSchemas.contains(schemaName)) {
        return List.of("Schema: " + schemaName);
      }

      // Otherwise, dig deeper into the ref
      visited.add(schemaName);
      Schema<?> resolvedSchema = openApi.getComponents().getSchemas().get(schemaName);
      List<String> childLeak =
          findSensitiveLeak(resolvedSchema, sensitiveSchemas, openApi, visited);
      visited.remove(schemaName);

      if (!childLeak.isEmpty()) {
        List<String> path = new ArrayList<>();
        path.add("Schema: " + schemaName);
        path.addAll(childLeak);
        return path;
      }
    }

    // 2. Check Array Items
    if (schema.getItems() != null) {
      List<String> itemsLeak =
          findSensitiveLeak(schema.getItems(), sensitiveSchemas, openApi, visited);
      if (!itemsLeak.isEmpty()) {
        return itemsLeak;
      }
    }

    // 3. Check Properties
    if (schema.getProperties() != null) {
      for (Map.Entry<String, Schema> entry : schema.getProperties().entrySet()) {
        String propName = entry.getKey();
        Schema propertySchema = entry.getValue();
        if (Boolean.TRUE.equals(propertySchema.getWriteOnly())) {
          continue;
        }
        // Direct property check
        if (isSensitiveWord(propName)) {
          return List.of("Property: " + propName);
        }

        // Recursive property check
        List<String> propLeak =
            findSensitiveLeak(entry.getValue(), sensitiveSchemas, openApi, visited);
        if (!propLeak.isEmpty()) {
          List<String> path = new ArrayList<>();
          path.add("Property: " + propName);
          path.addAll(propLeak);
          return path;
        }
      }
    }
    return Collections.emptyList();
  }
}
