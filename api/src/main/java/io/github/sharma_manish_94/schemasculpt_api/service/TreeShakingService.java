package io.github.sharma_manish_94.schemasculpt_api.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.swagger.v3.oas.models.*;
import io.swagger.v3.oas.models.media.Schema;
import java.util.*;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

@Service
@Slf4j
public class TreeShakingService {
  private final ObjectMapper objectMapper;

  public TreeShakingService(ObjectMapper objectMapper) {
    this.objectMapper = objectMapper;
  }

  public OpenAPI extractOperationWithDependencies(OpenAPI fullSpec, String path, String method) {
    if (fullSpec == null || fullSpec.getPaths() == null) {
      return null;
    }
    PathItem pathItem = fullSpec.getPaths().get(path);
    if (null == pathItem) {
      return null;
    }

    Operation operation =
        pathItem.readOperationsMap().get(PathItem.HttpMethod.valueOf(method.toUpperCase()));
    if (null == operation) {
      return null;
    }

    Set<String> allDependencies = findDependencies(operation, fullSpec);

    // Create a clean OpenAPI response that will serialize properly
    try {
      // Convert to JSON and back to ensure clean serialization
      String fullSpecJson = objectMapper.writeValueAsString(fullSpec);
      OpenAPI cleanFullSpec = objectMapper.readValue(fullSpecJson, OpenAPI.class);

      // Extract only what we need
      OpenAPI miniSpec = new OpenAPI();
      miniSpec.setOpenapi(cleanFullSpec.getOpenapi());
      miniSpec.setInfo(cleanFullSpec.getInfo());

      // Create clean paths with only the requested operation
      Paths cleanPaths = new Paths();
      PathItem cleanPathItem = new PathItem();
      cleanPathItem.operation(PathItem.HttpMethod.valueOf(method.toUpperCase()), operation);
      cleanPaths.addPathItem(path, cleanPathItem);
      miniSpec.setPaths(cleanPaths);

      // Add only required components
      if (!allDependencies.isEmpty()
          && cleanFullSpec.getComponents() != null
          && cleanFullSpec.getComponents().getSchemas() != null) {
        Components cleanComponents = new Components();
        Map<String, Schema> originalSchemas = cleanFullSpec.getComponents().getSchemas();
        for (String referencedSchema : allDependencies) {
          if (originalSchemas.containsKey(referencedSchema)) {
            cleanComponents.addSchemas(referencedSchema, originalSchemas.get(referencedSchema));
          }
        }
        miniSpec.setComponents(cleanComponents);
      }

      return miniSpec;
    } catch (Exception e) {
      log.error("Error creating clean tree-shaken spec", e);
      // Fallback to original implementation
      return createFallbackSpec(fullSpec, path, method, operation, allDependencies);
    }
  }

  private OpenAPI createFallbackSpec(
      OpenAPI fullSpec,
      String path,
      String method,
      Operation operation,
      Set<String> allDependencies) {
    Components newComponents = new Components();
    if (fullSpec.getComponents() != null && fullSpec.getComponents().getSchemas() != null) {
      Map<String, Schema> originalSchemas = fullSpec.getComponents().getSchemas();
      for (String referencedSchema : allDependencies) {
        if (originalSchemas.containsKey(referencedSchema)) {
          newComponents.addSchemas(referencedSchema, originalSchemas.get(referencedSchema));
        }
      }
    }
    OpenAPI miniSpec = new OpenAPI();
    miniSpec.setInfo(fullSpec.getInfo());
    miniSpec.setPaths(new Paths());
    PathItem newPathItem = new PathItem();
    newPathItem.operation(PathItem.HttpMethod.valueOf(method.toUpperCase()), operation);
    miniSpec.getPaths().addPathItem(path, newPathItem);
    miniSpec.setComponents(newComponents);
    return miniSpec;
  }

  private Set<String> findDependencies(Operation operation, OpenAPI fullSpec) {
    Set<String> foundRefs = new HashSet<>();
    Queue<JsonNode> nodesToVisit = new LinkedList<>();
    nodesToVisit.add(objectMapper.valueToTree(operation));
    while (!nodesToVisit.isEmpty()) {
      JsonNode currentNode = nodesToVisit.poll();
      if (currentNode.isObject()) {
        currentNode
            .properties()
            .forEach(
                property -> {
                  if ("$ref".equals(property.getKey()) && property.getValue().isTextual()) {
                    String refPath = property.getValue().asText();
                    String schemaName = refPath.substring("#/components/schemas/".length());
                    if (!foundRefs.contains(schemaName)) {
                      foundRefs.add(schemaName);
                      Schema schemaDef = fullSpec.getComponents().getSchemas().get(schemaName);
                      if (schemaDef != null) {
                        nodesToVisit.add(objectMapper.valueToTree(schemaDef));
                      }
                    }
                  } else {
                    nodesToVisit.add(property.getValue());
                  }
                });
      } else if (currentNode.isArray()) {
        currentNode.forEach(nodesToVisit::add);
      }
    }
    return foundRefs;
  }
}
