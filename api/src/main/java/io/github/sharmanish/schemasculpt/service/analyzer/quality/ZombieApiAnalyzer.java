package io.github.sharmanish.schemasculpt.service.analyzer.quality;

import io.github.sharmanish.schemasculpt.dto.analysis.ZombieApiResponse;
import io.github.sharmanish.schemasculpt.service.analyzer.base.AbstractSchemaAnalyzer;
import io.swagger.v3.oas.models.OpenAPI;
import org.springframework.stereotype.Component;

import java.util.ArrayList;
import java.util.List;

/**
 * Analyzer that detects unreachable or dead API endpoints.
 *
 * <p>Detects two types of "zombie" APIs:
 *
 * <ul>
 *   <li><b>Shadowed paths</b>: Static paths that are unreachable due to parameterized paths (e.g.,
 *       /users/{id} shadows /users/current)
 *   <li><b>Orphaned operations</b>: Endpoints with no parameters, request body, or response
 *       content
 * </ul>
 */
@Component
public class ZombieApiAnalyzer extends AbstractSchemaAnalyzer<ZombieApiResponse> {

  @Override
  protected ZombieApiResponse performAnalysis(OpenAPI openApi) {
    List<ZombieApiResponse.ZombieEndpoint> shadowed = new ArrayList<>();
    List<String> orphaned = new ArrayList<>();

    if (openApi.getPaths() == null) {
      return new ZombieApiResponse(shadowed, orphaned);
    }

    List<String> paths = new ArrayList<>(openApi.getPaths().keySet());

    // A. Shadow Detection (Parameterized paths vs. Static paths)
    for (String pathA : paths) {
      for (String pathB : paths) {
        if (pathA.equals(pathB)) {
          continue;
        }

        // Check if pathA (e.g., /users/{id}) shadows pathB (e.g., /users/current)
        if (isShadowing(pathA, pathB)) {
          shadowed.add(
              new ZombieApiResponse.ZombieEndpoint(
                  pathB,
                  pathA,
                  "Path "
                      + pathB
                      + " may be unreachable because it is shadowed by the parameterized path "
                      + pathA));
        }
      }
    }

    // B. Orphaned Operations (Empty returns/inputs)
    openApi
        .getPaths()
        .forEach(
            (path, pathItem) -> {
              pathItem
                  .readOperationsMap()
                  .forEach(
                      (method, operation) -> {
                        boolean hasParams =
                            operation.getParameters() != null
                                && !operation.getParameters().isEmpty();
                        boolean hasBody = operation.getRequestBody() != null;
                        boolean hasContent = false;

                        if (operation.getResponses() != null) {
                          // Check if 200 OK has content
                          var success = operation.getResponses().get("200");
                          if (success != null && success.getContent() != null) {
                            hasContent = true;
                          }
                        }

                        if (!hasParams && !hasBody && !hasContent) {
                          orphaned.add(method.name() + " " + path);
                        }
                      });
            });

    return new ZombieApiResponse(shadowed, orphaned);
  }

  /**
   * Checks if one path shadows another.
   *
   * @param genericPath Path with parameter (e.g., /users/{id})
   * @param specificPath Path with static segment (e.g., /users/current)
   * @return true if genericPath shadows specificPath
   */
  private boolean isShadowing(String genericPath, String specificPath) {
    String[] genParts = genericPath.split("/");
    String[] specParts = specificPath.split("/");

    if (genParts.length != specParts.length) {
      return false;
    }

    boolean possibleShadow = false;
    for (int i = 0; i < genParts.length; i++) {
      String genPart = genParts[i];
      String specPart = specParts[i];

      if (genPart.startsWith("{") && genPart.endsWith("}")) {
        // This is a parameter in the generic path.
        // If the specific path has a concrete string here, it's a potential collision.
        possibleShadow = true;
      } else if (!genPart.equals(specPart)) {
        // Static parts don't match (e.g., /users vs /products), so no shadow.
        return false;
      }
    }
    return possibleShadow;
  }
}
