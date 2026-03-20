package io.github.sharmanish.schemasculpt.service.analyzer.security;

import io.github.sharmanish.schemasculpt.dto.analysis.AuthzMatrixResponse;
import io.github.sharmanish.schemasculpt.service.analyzer.base.AbstractSchemaAnalyzer;
import io.swagger.v3.oas.models.OpenAPI;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.TreeSet;
import org.springframework.stereotype.Component;

/**
 * Analyzer that generates an authorization matrix showing required scopes for each operation.
 *
 * <p>Extracts security requirements from operation-level and global security definitions to create
 * a comprehensive view of access control across the API.
 *
 * <p>Operations without security requirements are marked as "PUBLIC".
 */
@Component
public class AuthorizationMatrixAnalyzer extends AbstractSchemaAnalyzer<AuthzMatrixResponse> {

  @Override
  protected AuthzMatrixResponse performAnalysis(OpenAPI openApi) {
    Set<String> allUniqueScopes = new TreeSet<>(); // Sorted for UI columns
    Map<String, List<String>> matrix = new LinkedHashMap<>();

    if (openApi.getPaths() != null) {
      openApi
          .getPaths()
          .forEach(
              (path, pathItem) -> {
                pathItem
                    .readOperationsMap()
                    .forEach(
                        (method, operation) -> {
                          String opKey = method.name() + " " + path;
                          List<String> opScopes = new ArrayList<>();

                          // 1. Check Operation-level security
                          if (operation.getSecurity() != null
                              && !operation.getSecurity().isEmpty()) {
                            operation
                                .getSecurity()
                                .forEach(
                                    requirement -> {
                                      requirement.forEach(
                                          (scheme, scopes) -> {
                                            allUniqueScopes.addAll(scopes);
                                            opScopes.addAll(scopes);
                                          });
                                    });
                          }
                          // 2. Fallback to Global security if operation
                          // level is missing
                          else if (openApi.getSecurity() != null
                              && !openApi.getSecurity().isEmpty()) {
                            openApi
                                .getSecurity()
                                .forEach(
                                    requirement -> {
                                      requirement.forEach(
                                          (scheme, scopes) -> {
                                            allUniqueScopes.addAll(scopes);
                                            opScopes.addAll(scopes);
                                          });
                                    });
                          } else {
                            opScopes.add("PUBLIC"); // Mark as public if no
                            // security
                            allUniqueScopes.add("PUBLIC");
                          }

                          matrix.put(opKey, opScopes);
                        });
              });
    }
    return new AuthzMatrixResponse(new ArrayList<>(allUniqueScopes), matrix);
  }
}
