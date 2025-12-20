package io.github.sharmanish.schemasculpt.service;

import io.github.sharmanish.schemasculpt.dto.diff.DiffEntry;
import io.github.sharmanish.schemasculpt.dto.diff.DiffResult;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.Operation;
import io.swagger.v3.oas.models.PathItem;
import io.swagger.v3.oas.models.media.Schema;
import io.swagger.v3.oas.models.parameters.Parameter;
import io.swagger.v3.oas.models.parameters.RequestBody;
import io.swagger.v3.oas.models.responses.ApiResponse;
import io.swagger.v3.oas.models.responses.ApiResponses;
import io.swagger.v3.parser.OpenAPIV3Parser;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.*;

@Slf4j
@Service
@RequiredArgsConstructor
public class SchemaDiffService {

  private final TreeDistanceService treeDistanceService;

  public static final String REMOVED = "Removed";
  public static final String PARAM_POINTER = " -> param:";

  /**
   * @param oldSpecContent original specification
   * @param newSpecContent specification after modification
   * @return difference in schema - both qualitative and quantitative
   */
  public DiffResult compareSpecs(String oldSpecContent, String newSpecContent) {
    OpenAPI oldSpec = new OpenAPIV3Parser().readContents(oldSpecContent, null, null)
        .getOpenAPI();
    OpenAPI newSpec = new OpenAPIV3Parser().readContents(newSpecContent, null, null)
        .getOpenAPI();

    if (oldSpec == null || newSpec == null) {
      throw new IllegalArgumentException("One or both API specifications could not be parsed.");
    }

    List<DiffEntry> diffs = new ArrayList<>();
    comparePaths(oldSpec, newSpec, diffs);
    compareComponentSchemas(oldSpec, newSpec, diffs);

    int breaking = (int) diffs.stream()
        .filter(d -> d.getType() == DiffEntry.ChangeType.BREAKING).count();
    int dangerous = (int) diffs.stream()
        .filter(d -> d.getType() == DiffEntry.ChangeType.DANGEROUS).count();
    int safe = (int) diffs.stream()
        .filter(d -> d.getType() == DiffEntry.ChangeType.SAFE).count();

    double distance = treeDistanceService.calculateSpecDistance(oldSpec, newSpec);
    String summary = classifyEvolution(breaking, distance);
    return DiffResult.builder()
        .changes(diffs)
        .breakingCount(breaking)
        .dangerousCount(dangerous)
        .safeCount(safe)
        .structuralDriftScore(distance)
        .evolutionSummary(summary)
        .build();
  }

  private String classifyEvolution(int breakingCount, double distance) {
    if (breakingCount > 0) {
      return "Breaking Update (Action Required)";
    }
    if (distance > 50.0) {
      return "Major Refactor (Safe)";
    }
    if (distance > 10.0) {
      return "Feature Update";
    }
    if (distance > 0.0) {
      return "Minor Patch";
    }
    return "No Structural Changes";
  }

  private void comparePaths(OpenAPI oldSpec, OpenAPI newSpec, List<DiffEntry> diffs) {
    if (oldSpec.getPaths() == null) {
      return;
    }

    oldSpec.getPaths().forEach((pathUrl, oldPathItem) -> {
      PathItem newPathItem = newSpec.getPaths() != null ? newSpec.getPaths().get(pathUrl) : null;

      if (newPathItem == null) {
        diffs.add(createDiff(pathUrl, DiffEntry.ChangeType.BREAKING, "PATH_REMOVED",
            "Path removed from specification", "Present", REMOVED));
      } else {
        compareOperations(pathUrl, oldPathItem.readOperationsMap(),
            newPathItem.readOperationsMap(), diffs);
      }
    });
  }

  private void compareOperations(String pathUrl,
                                 Map<PathItem.HttpMethod, Operation> oldOps,
                                 Map<PathItem.HttpMethod, Operation> newOps,
                                 List<DiffEntry> diffs) {
    oldOps.forEach((method, oldOp) -> {
      Operation newOp = newOps.get(method);
      String opId = method + " " + pathUrl;

      if (newOp == null) {
        diffs.add(createDiff(opId, DiffEntry.ChangeType.BREAKING, "OPERATION_REMOVED",
            "HTTP Method removed", method.toString(), REMOVED));
      } else {
        compareParameters(opId, oldOp.getParameters(), newOp.getParameters(), diffs);
        compareResponses(opId, oldOp.getResponses(), newOp.getResponses(), diffs);
        compareRequestBody(opId, oldOp.getRequestBody(), newOp.getRequestBody(), diffs);
      }
    });
  }

  private void compareParameters(String context, List<Parameter> oldParams,
                                 List<Parameter> newParams, List<DiffEntry> diffs) {
    List<Parameter> safeOldParams = oldParams == null ? Collections.emptyList() : oldParams;
    List<Parameter> safeNewParams = newParams == null ? Collections.emptyList() : newParams;

    for (Parameter oldP : safeOldParams) {
      checkForRemovedParams(context, diffs, oldP, safeNewParams);
    }
    for (Parameter newP : safeNewParams) {
      checkForAddedParams(context, diffs, newP, safeOldParams);
    }
  }

  private void checkForAddedParams(String context,
                                   List<DiffEntry> diffs,
                                   Parameter newP,
                                   List<Parameter> safeOldParams) {
    boolean existsInOld = safeOldParams.stream()
        .anyMatch(p -> p.getName().equals(newP.getName())
            && p.getIn().equals(newP.getIn()));

    if (!existsInOld) {
      // BREAKING: If new param is REQUIRED. SAFE if OPTIONAL.
      if (Boolean.TRUE.equals(newP.getRequired())) {
        diffs.add(createDiff(context + PARAM_POINTER + newP.getName(),
            DiffEntry.ChangeType.BREAKING, "NEW_REQUIRED_PARAM",
            "New Required parameter added", "None", "Required"));
      } else {
        diffs.add(createDiff(context + PARAM_POINTER + newP.getName(),
            DiffEntry.ChangeType.SAFE, "NEW_OPTIONAL_PARAM",
            "New Optional parameter added", "None", "Optional"));
      }
    }
  }

  private void checkForRemovedParams(String context,
                                     List<DiffEntry> diffs,
                                     Parameter oldParameter,
                                     List<Parameter> safeNewParams) {
    Optional<Parameter> newParameter = safeNewParams.stream()
        .filter(p -> p.getName().equals(oldParameter.getName())
            && p.getIn().equals(oldParameter.getIn()))
        .findFirst();

    if (newParameter.isEmpty()) {
      // BREAKING: If a parameter is removed, clients sending it might get errors
      // (or it's just ignored)
      // Usually considered Breaking if it was Required.
      DiffEntry.ChangeType type = Boolean.TRUE.equals(oldParameter.getRequired())
          ? DiffEntry.ChangeType.BREAKING : DiffEntry.ChangeType.SAFE;

      diffs.add(createDiff(context + PARAM_POINTER + oldParameter.getName(), type,
          "PARAM_REMOVED",
          "Parameter removed", oldParameter.getName(), REMOVED));
    } else {
      // Check if 'required' status changed
      boolean oldReq = Boolean.TRUE.equals(oldParameter.getRequired());
      boolean newReq = Boolean.TRUE.equals(newParameter.get().getRequired());

      if (!oldReq && newReq) {
        diffs.add(createDiff(context + PARAM_POINTER + oldParameter.getName(),
            DiffEntry.ChangeType.BREAKING, "PARAM_REQUIRED",
            "Optional parameter became Required", "Optional", "Required"));
      }
    }
  }

  private void compareResponses(String context,
                                ApiResponses oldResponse,
                                ApiResponses newResponse,
                                List<DiffEntry> diffs) {
    if (oldResponse == null) {
      return;
    }

    // Check for removed response codes
    oldResponse.forEach((code, response) -> {
      if (newResponse == null || !newResponse.containsKey(code)) {
        // Removing a success code (2xx) is BREAKING. Removing an error code is usually INFO/SAFE.
        boolean isSuccess = code.startsWith("2");
        DiffEntry.ChangeType type = isSuccess
            ? DiffEntry.ChangeType.BREAKING
            : DiffEntry.ChangeType.INFO;

        diffs.add(createDiff(context + " -> " + code, type, "RESPONSE_REMOVED",
            "Response code removed", code, REMOVED));
      } else {
        // Compare Content (Schemas)
        if (response.getContent() != null && newResponse.get(code).getContent() != null) {
          // Typically APIs have 'application/json'
          compareApplicationJsonResponseSchemaContent(context, newResponse, diffs, code, response);
        }
      }
    });
  }

  private void compareApplicationJsonResponseSchemaContent(String context,
                                                           ApiResponses newResponse,
                                                           List<DiffEntry> diffs,
                                                           String code,
                                                           ApiResponse response) {
    String mediaType = "application/json";
    if (response.getContent().containsKey(mediaType)
        && newResponse.get(code).getContent().containsKey(mediaType)) {
      Schema<?> oldSchema = response.getContent().get(mediaType).getSchema();
      Schema<?> newSchema = newResponse.get(code).getContent().get(mediaType).getSchema();
      compareSchemas(context + " -> " + code,
          oldSchema, newSchema, diffs, true); // true = Response Context
    }
  }

  private void compareRequestBody(String context,
                                  RequestBody oldReq,
                                  RequestBody newReq,
                                  List<DiffEntry> diffs) {
    if (oldReq == null) {
      return;
    }
    if (newReq == null) {
      diffs.add(createDiff(context + " -> body",
          DiffEntry.ChangeType.SAFE,
          "BODY_REMOVED",
          "Request body removed",
          "Present", REMOVED));
      return;
    }

    String mediaType = "application/json";
    if (oldReq.getContent() != null && oldReq.getContent().containsKey(mediaType)
        && newReq.getContent() != null && newReq.getContent().containsKey(mediaType)) {
      Schema<?> oldS = oldReq.getContent().get(mediaType).getSchema();
      Schema<?> newS = newReq.getContent().get(mediaType).getSchema();
      compareSchemas(context + " -> requestBody", oldS, newS, diffs,
          false); // false = Request Context
    }
  }

  /**
   * Deep Recursive Schema Comparison
   *
   * @param isResponseContext - TRUE if comparing a Response Body,
   *                          FALSE if comparing a Request Body.
   *                          This distinction is crucial:
   *                          Adding a field to a Request is BREAKING (if required),
   *                          adding to Response is SAFE.
   */
  private void compareSchemas(String context,
                              Schema<?> oldSchema,
                              Schema<?> newSchema,
                              List<DiffEntry> diffs,
                              boolean isResponseContext) {
    if (oldSchema == null || newSchema == null) {
      return;
    }

    if (isTypeChanged(context, oldSchema, newSchema, diffs)) {
      return; // Stop processing children if type changed completely (e.g. Object -> Array)
    }

    // 2. Property Comparison (For Objects)
    if (oldSchema.getProperties() != null) {
      Map<String, Schema> newProps = newSchema.getProperties() != null
          ? newSchema.getProperties()
          : Collections.emptyMap();
      checkRemovedProperties(context, oldSchema, diffs, isResponseContext, newProps);
      checkAddedProperties(context, oldSchema, newSchema, diffs, isResponseContext, newProps);
    }
  }

  private void checkAddedProperties(String context,
                                    Schema<?> oldSchema,
                                    Schema<?> newSchema,
                                    List<DiffEntry> diffs,
                                    boolean isResponseContext,
                                    Map<String, Schema> newProps) {
    newProps.forEach((name, schema) -> {
      if (!oldSchema.getProperties().containsKey(name)) {
        // If Response: SAFE (Client receives extra data, usually ignores it).
        // If Request: BREAKING if Required, SAFE if Optional.
        if (isResponseContext) {
          diffs.add(createDiff(context + "." + name, DiffEntry.ChangeType.SAFE,
              "PROPERTY_ADDED",
              "New property added to response", "None", name));
        } else {
          checkRequiredAddedProperties(context, newSchema, diffs, name);
        }
      }
    });
  }

  private void checkRequiredAddedProperties(String context,
                                            Schema<?> newSchema,
                                            List<DiffEntry> diffs,
                                            String name) {
    List<String> required = newSchema.getRequired() != null
        ? newSchema.getRequired()
        : Collections.emptyList();
    if (required.contains(name)) {
      diffs.add(createDiff(context + "." + name, DiffEntry.ChangeType.BREAKING,
          "REQUIRED_PROPERTY_ADDED",
          "New required property added to request",
          "None", name));
    } else {
      diffs.add(createDiff(context + "." + name, DiffEntry.ChangeType.SAFE,
          "OPTIONAL_PROPERTY_ADDED",
          "New optional property added to request",
          "None", name));
    }
  }

  private void checkRemovedProperties(String context,
                                      Schema<?> oldSchema,
                                      List<DiffEntry> diffs,
                                      boolean isResponseContext,
                                      Map<String, Schema> newProps) {
    // A. Check Removed Properties
    oldSchema.getProperties().forEach((name, schema) -> {
      if (!newProps.containsKey(name)) {
        // BREAKING if in Response (Client expects it).
        // SAFE if in Request (Server just stops using it).
        DiffEntry.ChangeType type = isResponseContext
            ? DiffEntry.ChangeType.BREAKING
            : DiffEntry.ChangeType.SAFE;
        diffs.add(createDiff(context + "." + name, type, "PROPERTY_REMOVED",
            "Property removed from schema", name, REMOVED));
      } else {
        compareSchemas(context + "." + name, schema, newProps.get(name),
            diffs,
            isResponseContext);
      }
    });
  }

  private boolean isTypeChanged(String context,
                                Schema<?> oldSchema,
                                Schema<?> newSchema,
                                List<DiffEntry> diffs) {
    if (!Objects.equals(oldSchema.getType(), newSchema.getType())) {
      diffs.add(createDiff(context, DiffEntry.ChangeType.BREAKING, "TYPE_CHANGED",
          "Data type changed", oldSchema.getType(), newSchema.getType()));
      return true;
    }
    return false;
  }

  private void compareComponentSchemas(OpenAPI oldSpec, OpenAPI newSpec, List<DiffEntry> diffs) {
    if (oldSpec.getComponents() == null || oldSpec.getComponents().getSchemas() == null) {
      return;
    }

    oldSpec.getComponents().getSchemas().forEach((name, oldSchema) -> {
      if (newSpec.getComponents() != null && newSpec.getComponents().getSchemas() != null) {
        Schema<?> newSchema = newSpec.getComponents().getSchemas().get(name);
        if (newSchema == null) {
          // Schema removed from definitions.
          // This is only INFO unless it was used, but usage is checked in comparePaths.
          diffs.add(createDiff("Schema: " + name, DiffEntry.ChangeType.INFO,
              "SCHEMA_REMOVED",
              "Schema definition removed", name, REMOVED));
        } else {
          // We treat Component schemas as "Response Context" by default for safety,
          // or we can skip this and rely on comparePaths to catch actual usage.
          // For deep analysis, let's just log structural changes as INFO/DANGEROUS
          // since we don't know the context (Request vs Response) here.
        }
      }
    });
  }

  private DiffEntry createDiff(final String id,
                               final DiffEntry.ChangeType type,
                               final String category,
                               final String msg,
                               final String oldValue,
                               final String newValue) {
    return DiffEntry.builder()
        .id(id)
        .type(type)
        .category(category)
        .message(msg)
        .oldValue(oldValue)
        .newValue(newValue)
        .build();
  }
}
