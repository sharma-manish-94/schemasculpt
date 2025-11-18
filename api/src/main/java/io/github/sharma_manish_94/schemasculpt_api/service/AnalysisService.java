package io.github.sharma_manish_94.schemasculpt_api.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.github.sharma_manish_94.schemasculpt_api.dto.analysis.AuthzMatrixResponse;
import io.github.sharma_manish_94.schemasculpt_api.dto.analysis.SchemaSimilarityResponse;
import io.github.sharma_manish_94.schemasculpt_api.dto.analysis.TaintAnalysisResponse;
import io.github.sharma_manish_94.schemasculpt_api.dto.analysis.ZombieApiResponse;
import io.swagger.v3.oas.models.Components;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.Operation;
import io.swagger.v3.oas.models.media.Schema;
import io.swagger.v3.oas.models.parameters.RequestBody;
import io.swagger.v3.parser.OpenAPIV3Parser;
import io.swagger.v3.parser.core.models.ParseOptions;
import io.swagger.v3.parser.core.models.SwaggerParseResult;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.*;

@Slf4j
@Service
public class AnalysisService {

    private static final String COMPONENTS_SCHEMAS_PREFIX = "#/components/schemas/";
    private static final String OPERATION_PREFIX = "Operations: ";
    private static final String SCHEMA_PREFIX = "Schema: ";
    private static final Set<String> SENSITIVE_KEYWORDS = Set.of(
            "password", "secret", "token", "key", "ssn", "socialsecurity",
            "creditcard", "cardnumber", "cvv", "pii", "salary", "internal"
    );
    private final ObjectMapper objectMapper;

    public AnalysisService(ObjectMapper objectMapper) {
        this.objectMapper = objectMapper;
    }

    /**
     * Builds a map where the key is a component name and the value is a set of all other
     * components/operations that depend on it.
     */
    public Map<String, Set<String>> buildReverseDependencyGraph(OpenAPI openApi) {
        Map<String, Set<String>> reverseGraph = new HashMap<>();

        Map<String, Schema> allSchemas =
                Optional.ofNullable(openApi.getComponents())
                        .map(Components::getSchemas)
                        .orElse(Collections.emptyMap());
        if (allSchemas.isEmpty()) {
            return reverseGraph;
        }

        allSchemas.keySet().forEach(schemaName -> reverseGraph.put(schemaName, new HashSet<>()));

        if (Objects.nonNull(openApi.getPaths())) {
            openApi
                    .getPaths()
                    .forEach(
                            (pathName, pathItem) -> {
                                pathItem
                                        .readOperationsMap()
                                        .forEach(
                                                (httpMethod, operation) -> {
                                                    String dependantName = OPERATION_PREFIX + httpMethod + " " + pathName;
                                                    findRefsInOperation(operation, dependantName, reverseGraph);
                                                });
                            });
        }

        allSchemas.forEach(
                (schemaName, schema) -> {
                    String dependantName = SCHEMA_PREFIX + schemaName;
                    findRefsInSchema(schema, dependantName, reverseGraph, new HashSet<>());
                });

        return reverseGraph;
    }

    /**
     * Scans an operation's request bodies and responses for schema references
     *
     * @param operation     operation for which request and response schema is being scanned
     * @param dependentName The name of the item that contains this schema (e.g., "Operation: GET
     *                      /users").
     * @param reverseGraph  The graph to populate.
     */
    private void findRefsInOperation(
            Operation operation, String dependentName, Map<String, Set<String>> reverseGraph) {
        Optional.ofNullable(operation.getRequestBody())
                .map(RequestBody::getContent)
                .ifPresent(
                        content ->
                                content
                                        .values()
                                        .forEach(
                                                mediaType ->
                                                        findRefsInSchema(
                                                                mediaType.getSchema(),
                                                                dependentName,
                                                                reverseGraph,
                                                                new HashSet<>())));
        Optional.ofNullable(operation.getResponses())
                .ifPresent(
                        apiResponses ->
                                apiResponses
                                        .values()
                                        .forEach(
                                                apiResponse -> {
                                                    Optional.ofNullable(apiResponse.getContent())
                                                            .ifPresent(
                                                                    content ->
                                                                            content
                                                                                    .values()
                                                                                    .forEach(
                                                                                            mediaType ->
                                                                                                    findRefsInSchema(
                                                                                                            mediaType.getSchema(),
                                                                                                            dependentName,
                                                                                                            reverseGraph,
                                                                                                            new HashSet<>())));
                                                }));
    }

    /**
     * Recursively finds all $ref links within a given Schema object and adds them to the graph.
     *
     * @param schema        The schema object to scan.
     * @param dependentName The name of the item that contains this schema (e.g., "Operation: GET
     *                      /users").
     * @param reverseGraph  The graph to populate.
     * @param visited       A set to track visited schemas and prevent infinite recursion in circular
     *                      models.
     */
    private void findRefsInSchema(
            Schema<?> schema,
            String dependentName,
            Map<String, Set<String>> reverseGraph,
            Set<Schema<?>> visited) {
        if (schema == null || visited.contains(schema)) {
            return;
        }
        visited.add(schema);
        processDirectReferences(schema, dependentName, reverseGraph);
        processObjectProperties(schema, dependentName, reverseGraph, visited);
        processArrayItems(schema, dependentName, reverseGraph, visited);
        processCompositeSchemas(schema, dependentName, reverseGraph, visited);
        visited.remove(schema);
    }

    private void processCompositeSchemas(
            Schema<?> schema,
            String dependentName,
            Map<String, Set<String>> reverseGraph,
            Set<Schema<?>> visited) {
        if (schema.getAllOf() != null) {
            schema.getAllOf().forEach(s -> findRefsInSchema(s, dependentName, reverseGraph, visited));
        }
        if (schema.getAnyOf() != null) {
            schema.getAnyOf().forEach(s -> findRefsInSchema(s, dependentName, reverseGraph, visited));
        }
        if (schema.getOneOf() != null) {
            schema.getOneOf().forEach(s -> findRefsInSchema(s, dependentName, reverseGraph, visited));
        }
    }

    private void processArrayItems(
            Schema<?> schema,
            String dependentName,
            Map<String, Set<String>> reverseGraph,
            Set<Schema<?>> visited) {
        if (schema.getItems() != null) {
            findRefsInSchema(schema.getItems(), dependentName, reverseGraph, visited);
        }
    }

    private void processObjectProperties(
            Schema<?> schema,
            String dependentName,
            Map<String, Set<String>> reverseGraph,
            Set<Schema<?>> visited) {
        if (schema.getProperties() != null) {
            schema
                    .getProperties()
                    .values()
                    .forEach(
                            propertySchema ->
                                    findRefsInSchema(propertySchema, dependentName, reverseGraph, visited));
        }
    }

    private void processDirectReferences(
            Schema<?> schema, String dependentName, Map<String, Set<String>> reverseGraph) {
        if (schema.get$ref() != null) {
            String refPath = schema.get$ref();
            if (refPath.startsWith(COMPONENTS_SCHEMAS_PREFIX)) {
                String schemaName = refPath.substring(COMPONENTS_SCHEMAS_PREFIX.length());
                reverseGraph.computeIfAbsent(schemaName, k -> new HashSet<>()).add(dependentName);
            }
        }
    }

    public Map<String, Integer> calculateAllDepths(String specText) {
        if (specText == null || specText.isEmpty()) {
            return Collections.emptyMap();
        }
        OpenAPI openApi = parseOpenApiSpec(specText);
        return calculateAllDepths(openApi);
    }

    public Map<String, Integer> calculateAllDepths(final OpenAPI openApi) {
        if (isOpenAPIInvalid(openApi)) {
            log.error("Parsed OpenAPI spec is null or has no paths");
            return Collections.emptyMap();
        }

        Map<String, Schema> allSchemas =
                Optional.ofNullable(openApi.getComponents())
                        .map(Components::getSchemas)
                        .orElse(Collections.emptyMap());
        return processAllOperations(openApi, allSchemas);
    }

    private boolean isOpenAPIInvalid(OpenAPI openApi) {
        return (openApi == null || openApi.getPaths() == null || openApi.getPaths().isEmpty());
    }

    private OpenAPI parseOpenApiSpec(String specText) {
        ParseOptions options = new ParseOptions();
        options.setResolve(false);

        SwaggerParseResult parseResult = new OpenAPIV3Parser().readContents(specText, null, options);

        if (parseResult.getMessages() != null && !parseResult.getMessages().isEmpty()) {
            log.warn("Warnings during OpenAPI parsing: " + parseResult.getMessages());
        }

        return parseResult.getOpenAPI();
    }

    private Map<String, Integer> processAllOperations(
            OpenAPI openApi, Map<String, Schema> allSchemas) {
        Map<String, Integer> allDepths = new HashMap<>();
        Map<String, Integer> memo = new HashMap<>();
        openApi
                .getPaths()
                .forEach(
                        (pathKey, pathItem) ->
                                pathItem
                                        .readOperationsMap()
                                        .forEach(
                                                (method, operation) -> {
                                                    String operationKey = method.toString() + " " + pathKey;
                                                    log.debug("Calculating depth for operation: " + operationKey);
                                                    JsonNode operationNode = objectMapper.valueToTree(operation);
                                                    int maxDepth =
                                                            calculateMaxDepth(operationNode, new HashSet<>(), allSchemas, memo);
                                                    allDepths.put(operationKey, maxDepth);
                                                }));

        return allDepths;
    }

    private int calculateMaxDepth(
            JsonNode node,
            Set<String> visited,
            Map<String, Schema> allSchemas,
            Map<String, Integer> memo) {
        if (node == null || !node.isContainerNode()) {
            return 0;
        }

        if (node.isObject() && node.has("$ref")) {
            String refPath = node.get("$ref").asText();
            if (refPath.startsWith(COMPONENTS_SCHEMAS_PREFIX)) {
                String schemaName = refPath.substring(COMPONENTS_SCHEMAS_PREFIX.length());

                if (memo.containsKey(schemaName)) {
                    return 1 + memo.get(schemaName);
                }
                if (visited.contains(schemaName)) {
                    return 0;
                }

                Schema schema = allSchemas.get(schemaName);
                if (schema == null) return 0;

                visited.add(schemaName);
                JsonNode schemaNode = objectMapper.valueToTree(schema);

                int nestedDepth = calculateMaxDepth(schemaNode, visited, allSchemas, memo);

                visited.remove(schemaName);

                memo.put(schemaName, nestedDepth);
                return 1 + nestedDepth;
            }
        }

        int maxDepth = 0;
        Iterator<JsonNode> elements = node.elements();
        while (elements.hasNext()) {
            int childDepth = calculateMaxDepth(elements.next(), new HashSet<>(visited), allSchemas, memo);
            maxDepth = Math.max(maxDepth, childDepth);
        }
        return maxDepth;
    }

    public int calculateNestingDepthForOperation(Operation operation, OpenAPI openApi) {
        if (operation == null || openApi == null || openApi.getComponents() == null) {
            return 0;
        }

        Map<String, Schema> allSchemas =
                Optional.ofNullable(openApi.getComponents())
                        .map(Components::getSchemas)
                        .orElse(Collections.emptyMap());

        JsonNode operationNode = objectMapper.valueToTree(operation);
        Map<String, Integer> memo = new HashMap<>();

        return calculateMaxDepth(operationNode, new HashSet<>(), allSchemas, memo);
    }

    public AuthzMatrixResponse generateAuthzMatrix(OpenAPI openApi) {
        Set<String> allUniqueScopes = new TreeSet<>(); // Sorted for UI columns
        Map<String, List<String>> matrix = new LinkedHashMap<>();

        if (openApi.getPaths() != null) {
            openApi.getPaths().forEach((path, pathItem) -> {
                pathItem.readOperationsMap().forEach((method, operation) -> {
                    String opKey = method.name() + " " + path;
                    List<String> opScopes = new ArrayList<>();

                    // 1. Check Operation-level security
                    if (operation.getSecurity() != null && !operation.getSecurity().isEmpty()) {
                        operation.getSecurity().forEach(requirement -> {
                            requirement.forEach((scheme, scopes) -> {
                                allUniqueScopes.addAll(scopes);
                                opScopes.addAll(scopes);
                            });
                        });
                    }
                    // 2. Fallback to Global security if operation level is missing
                    else if (openApi.getSecurity() != null && !openApi.getSecurity().isEmpty()) {
                        openApi.getSecurity().forEach(requirement -> {
                            requirement.forEach((scheme, scopes) -> {
                                allUniqueScopes.addAll(scopes);
                                opScopes.addAll(scopes);
                            });
                        });
                    } else {
                        opScopes.add("PUBLIC"); // Mark as public if no security
                        allUniqueScopes.add("PUBLIC");
                    }

                    matrix.put(opKey, opScopes);
                });
            });
        }
        return new AuthzMatrixResponse(new ArrayList<>(allUniqueScopes), matrix);
    }

    public TaintAnalysisResponse performTaintAnalysis(OpenAPI openApi) {
        List<TaintAnalysisResponse.TaintVulnerability> vulnerabilities = new ArrayList<>();

        // Step A: Identify Sources (Schemas that contain sensitive data)
        Set<String> sensitiveSchemas = identifySensitiveSchemas(openApi);

        if (openApi.getPaths() != null) {
            openApi.getPaths().forEach((path, pathItem) -> {
                pathItem.readOperationsMap().forEach((method, operation) -> {
                    // Step B: Check Barriers (Is the endpoint secured?)
                    boolean isSecured = isOperationSecured(operation, openApi);

                    // Step C: Check Sinks (Responses)
                    if (operation.getResponses() != null) {
                        operation.getResponses().forEach((statusCode, response) -> {
                            if (response.getContent() != null) {
                                response.getContent().forEach((mediaType, content) -> {
                                    Schema<?> schema = content.getSchema();
                                    if (schema != null) {
                                        // Traversal: Check if response flows from a sensitive source
                                        List<String> leakTrail = findSensitiveLeak(schema, sensitiveSchemas, openApi, new HashSet<>());

                                        if (!leakTrail.isEmpty()) {
                                            String trailString = String.join(" -> ", leakTrail);

                                            if (!isSecured) {
                                                // CRITICAL: Sensitive data on public endpoint
                                                vulnerabilities.add(new TaintAnalysisResponse.TaintVulnerability(
                                                        method.name() + " " + path,
                                                        "CRITICAL",
                                                        "Public endpoint returning sensitive data (Data Leakage)",
                                                        trailString
                                                ));
                                            } else {
                                                // WARNING: Sensitive data returned, verified security needed
                                                vulnerabilities.add(new TaintAnalysisResponse.TaintVulnerability(
                                                        method.name() + " " + path,
                                                        "WARNING",
                                                        "Sensitive data exposure (Verify necessity)",
                                                        trailString
                                                ));
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

    // --- Taint Analysis Helpers ---

    private boolean isOperationSecured(Operation operation, OpenAPI openApi) {
        if (operation.getSecurity() != null && !operation.getSecurity().isEmpty()) {
            return true;
        }
        // If no operation security, check global security
        return openApi.getSecurity() != null && !openApi.getSecurity().isEmpty();
    }

    private Set<String> identifySensitiveSchemas(OpenAPI openApi) {
        Set<String> sensitiveSchemas = new HashSet<>();
        if (openApi.getComponents() == null || openApi.getComponents().getSchemas() == null) {
            return sensitiveSchemas;
        }

        openApi.getComponents().getSchemas().forEach((name, schema) -> {
            // 1. Check Schema Name (e.g., "CreditCard")
            if (isSensitiveWord(name)) {
                sensitiveSchemas.add(name);
            }
            // 2. Check Properties (e.g., "password")
            else if (schema.getProperties() != null) {
                boolean hasSensitiveProp = schema.getProperties().keySet().stream()
                        .anyMatch(key -> isSensitiveWord((String) key));
                if (hasSensitiveProp) {
                    sensitiveSchemas.add(name);
                }
            }
        });
        return sensitiveSchemas;
    }


    private boolean isSensitiveWord(String text) {
        if (text == null) return false;
        String lower = text.toLowerCase();
        return SENSITIVE_KEYWORDS.stream().anyMatch(lower::contains);
    }

    private List<String> findSensitiveLeak(Schema<?> schema, Set<String> sensitiveSchemas, OpenAPI openApi, Set<String> visited) {
        if (schema == null) return Collections.emptyList();

        // 1. Check $ref
        if (schema.get$ref() != null) {
            String schemaName = schema.get$ref().substring(schema.get$ref().lastIndexOf('/') + 1);

            if (visited.contains(schemaName)) return Collections.emptyList(); // Cycle detected

            // If this schema is marked sensitive, we found a leak!
            if (sensitiveSchemas.contains(schemaName)) {
                return List.of("Schema: " + schemaName);
            }

            // Otherwise, dig deeper into the ref
            visited.add(schemaName);
            Schema<?> resolvedSchema = openApi.getComponents().getSchemas().get(schemaName);
            List<String> childLeak = findSensitiveLeak(resolvedSchema, sensitiveSchemas, openApi, visited);
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
            List<String> itemsLeak = findSensitiveLeak(schema.getItems(), sensitiveSchemas, openApi, visited);
            if (!itemsLeak.isEmpty()) return itemsLeak;
        }

        // 3. Check Properties
        if (schema.getProperties() != null) {
            for (Map.Entry<String, Schema> entry : schema.getProperties().entrySet()) {
                String propName = entry.getKey();

                // Direct property check
                if (isSensitiveWord(propName)) {
                    return List.of("Property: " + propName);
                }

                // Recursive property check
                List<String> propLeak = findSensitiveLeak(entry.getValue(), sensitiveSchemas, openApi, visited);
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

    public SchemaSimilarityResponse analyzeSchemaSimilarity(OpenAPI openApi) {
        List<SchemaSimilarityResponse.SchemaCluster> clusters = new ArrayList<>();
        if (openApi.getComponents() == null || openApi.getComponents().getSchemas() == null) {
            return new SchemaSimilarityResponse(clusters);
        }

        Map<String, Schema> schemas = openApi.getComponents().getSchemas();
        List<String> schemaNames = new ArrayList<>(schemas.keySet());

        // Compare every schema against every other schema (O(n^2))
        // For large specs, we might want to limit this or optimize.
        Set<String> processed = new HashSet<>();

        for (int i = 0; i < schemaNames.size(); i++) {
            String nameA = schemaNames.get(i);
            if (processed.contains(nameA)) continue;

            Set<String> currentCluster = new HashSet<>();
            currentCluster.add(nameA);

            for (int j = i + 1; j < schemaNames.size(); j++) {
                String nameB = schemaNames.get(j);
                if (processed.contains(nameB)) continue;

                double similarity = calculateJaccardSimilarity(schemas.get(nameA), schemas.get(nameB));

                // Threshold: If 80% similar, group them
                if (similarity > 0.80) {
                    currentCluster.add(nameB);
                    processed.add(nameB);
                }
            }

            if (currentCluster.size() > 1) {
                clusters.add(new SchemaSimilarityResponse.SchemaCluster(
                        currentCluster,
                        0.80, // Simplified score for the group
                        "These schemas share >80% structure. Consider creating a base schema."
                ));
            }
        }
        return new SchemaSimilarityResponse(clusters);
    }

    private double calculateJaccardSimilarity(Schema schemaA, Schema schemaB) {
        // 1. Extract "features" (property names + types)
        Set<String> featuresA = extractSchemaFeatures(schemaA);
        Set<String> featuresB = extractSchemaFeatures(schemaB);

        if (featuresA.isEmpty() && featuresB.isEmpty()) return 1.0; // Both empty = identical
        if (featuresA.isEmpty() || featuresB.isEmpty()) return 0.0;

        // 2. Calculate Jaccard Index: (Intersection) / (Union)
        Set<String> intersection = new HashSet<>(featuresA);
        intersection.retainAll(featuresB);

        Set<String> union = new HashSet<>(featuresA);
        union.addAll(featuresB);

        return (double) intersection.size() / union.size();
    }

    private Set<String> extractSchemaFeatures(Schema schema) {
        Set<String> features = new HashSet<>();
        if (schema.getProperties() != null) {
            schema.getProperties().forEach((propName, propSchema) -> {
                String type = propSchema instanceof Schema ? ((Schema) propSchema).getType() : "unknown";
                features.add(propName + ":" + type);
            });
        }
        return features;
    }

    public ZombieApiResponse detectZombieApis(OpenAPI openApi) {
        List<ZombieApiResponse.ZombieEndpoint> shadowed = new ArrayList<>();
        List<String> orphaned = new ArrayList<>();

        if (openApi.getPaths() == null) return new ZombieApiResponse(shadowed, orphaned);

        List<String> paths = new ArrayList<>(openApi.getPaths().keySet());

        // A. Shadow Detection (Simplified: Parameterized paths vs. Static paths)
        for (String pathA : paths) {
            for (String pathB : paths) {
                if (pathA.equals(pathB)) continue;

                // Check if pathA (e.g., /users/{id}) shadows pathB (e.g., /users/current)
                if (isShadowing(pathA, pathB)) {
                    shadowed.add(new ZombieApiResponse.ZombieEndpoint(
                            pathB,
                            pathA,
                            "Path " + pathB + " may be unreachable because it is shadowed by the parameterized path " + pathA
                    ));
                }
            }
        }

        // B. Orphaned Operations (Empty returns/inputs)
        openApi.getPaths().forEach((path, pathItem) -> {
            pathItem.readOperationsMap().forEach((method, operation) -> {
                boolean hasParams = operation.getParameters() != null && !operation.getParameters().isEmpty();
                boolean hasBody = operation.getRequestBody() != null;
                boolean hasContent = false;

                if (operation.getResponses() != null) {
                    // Check if 200 OK has content
                    var success = operation.getResponses().get("200");
                    if (success != null && success.getContent() != null) hasContent = true;
                }

                if (!hasParams && !hasBody && !hasContent) {
                    orphaned.add(method.name() + " " + path);
                }
            });
        });

        return new ZombieApiResponse(shadowed, orphaned);
    }

    private boolean isShadowing(String genericPath, String specificPath) {
        // Logic: If genericPath has a parameter {x} and specificPath has a static segment
        // at the same position, it *might* be a shadow.
        // Example: /users/{id} vs /users/current

        String[] genParts = genericPath.split("/");
        String[] specParts = specificPath.split("/");

        if (genParts.length != specParts.length) return false;

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
