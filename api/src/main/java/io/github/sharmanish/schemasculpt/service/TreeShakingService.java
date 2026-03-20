package io.github.sharmanish.schemasculpt.service;

import io.swagger.v3.core.util.Json;
import io.swagger.v3.oas.models.Components;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.Operation;
import io.swagger.v3.oas.models.PathItem;
import io.swagger.v3.oas.models.Paths;
import io.swagger.v3.oas.models.media.Schema;
import java.util.HashSet;
import java.util.LinkedList;
import java.util.Locale;
import java.util.Map;
import java.util.Queue;
import java.util.Set;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

@Service
@Slf4j
public class TreeShakingService {

  public OpenAPI extractOperationWithDependencies(OpenAPI fullSpec, String path, String method) {
    if (fullSpec == null || fullSpec.getPaths() == null) {
      return null;
    }
    PathItem pathItem = fullSpec.getPaths().get(path);
    if (null == pathItem) {
      return null;
    }

    Operation operation =
        pathItem
            .readOperationsMap()
            .get(PathItem.HttpMethod.valueOf(method.toUpperCase(Locale.ROOT)));
    if (null == operation) {
      return null;
    }

    Set<String> allDependencies = findDependencies(operation, fullSpec);

    // Create a clean OpenAPI response that will serialize properly
    try {
      // CRITICAL: Use Swagger's internal mapper (Jackson 2) for OpenAPI models.
      // Jackson 3 doesn't yet support all Swagger custom deserializers (like additionalProperties).
      com.fasterxml.jackson.databind.ObjectMapper swaggerMapper = Json.mapper();

      // Convert to JSON and back to ensure clean serialization
      String fullSpecJson = swaggerMapper.writeValueAsString(fullSpec);
      OpenAPI cleanFullSpec = swaggerMapper.readValue(fullSpecJson, OpenAPI.class);

      // Extract only what we need
      OpenAPI miniSpec = new OpenAPI();
      miniSpec.setOpenapi(cleanFullSpec.getOpenapi());
      miniSpec.setInfo(cleanFullSpec.getInfo());

      // Create clean paths with only the requested operation
      Paths cleanPaths = new Paths();
      PathItem cleanPathItem = new PathItem();
      cleanPathItem.operation(
          PathItem.HttpMethod.valueOf(method.toUpperCase(Locale.ROOT)), operation);
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

  private Set<String> findDependencies(Operation operation, OpenAPI fullSpec) {
    Set<String> foundRefs = new HashSet<>();

    // Use Jackson 2 JsonNode for traversing Swagger models
    Queue<com.fasterxml.jackson.databind.JsonNode> nodesToVisit = new LinkedList<>();
    com.fasterxml.jackson.databind.ObjectMapper mapper = Json.mapper();

    nodesToVisit.add(mapper.valueToTree(operation));
    while (!nodesToVisit.isEmpty()) {
      com.fasterxml.jackson.databind.JsonNode currentNode = nodesToVisit.poll();
      if (currentNode.isObject()) {
        java.util.Iterator<Map.Entry<String, com.fasterxml.jackson.databind.JsonNode>> fields = currentNode.fields();
        while (fields.hasNext()) {
          Map.Entry<String, com.fasterxml.jackson.databind.JsonNode> property = fields.next();
          if ("$ref".equals(property.getKey()) && property.getValue().isTextual()) {
            String refPath = property.getValue().asText();
            if (refPath.startsWith("#/components/schemas/")) {
              String schemaName = refPath.substring("#/components/schemas/".length());
              if (!foundRefs.contains(schemaName)) {
                foundRefs.add(schemaName);
                Schema schemaDef = fullSpec.getComponents().getSchemas().get(schemaName);
                if (schemaDef != null) {
                  nodesToVisit.add(mapper.valueToTree(schemaDef));
                }
              }
            }
          } else {
            nodesToVisit.add(property.getValue());
          }
        }
      } else if (currentNode.isArray()) {
        currentNode.forEach(nodesToVisit::add);
      }
    }
    return foundRefs;
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
    newPathItem.operation(PathItem.HttpMethod.valueOf(method.toUpperCase(Locale.ROOT)), operation);
    miniSpec.getPaths().addPathItem(path, newPathItem);
    miniSpec.setComponents(newComponents);
    return miniSpec;
  }
}
