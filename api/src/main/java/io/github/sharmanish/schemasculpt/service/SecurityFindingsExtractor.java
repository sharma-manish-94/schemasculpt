package io.github.sharmanish.schemasculpt.service;

import io.github.sharmanish.schemasculpt.dto.analysis.SecurityFinding;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.Operation;
import io.swagger.v3.oas.models.media.Schema;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

/**
 * The "Linter-Augmented AI Analyst" - Security Findings Extractor.
 * <p>
 * This service extracts FACTUAL, DETERMINISTIC security findings from an OpenAPI spec.
 * Instead of sending a 5MB spec to the AI, we send only these pre-processed facts.
 * <p>
 * Java does what it's best at: Finding facts with 100% accuracy.
 * AI does what it's best at: Reasoning about attack chains and patterns.
 * <p>
 * This is the professional, scalable approach to AI-powered security analysis.
 */
@Slf4j
@Service
public class SecurityFindingsExtractor {

  private static final Set<String> SENSITIVE_KEYWORDS = Set.of(
      "password", "secret", "token", "key", "ssn", "socialsecurity",
      "creditcard", "cardnumber", "cvv", "pii", "salary", "internal",
      "role", "permission", "admin", "privilege"
  );

  private static final String COMPONENTS_SCHEMAS_PREFIX = "#/components/schemas/";

  /**
   * Main entry point: Extract all security findings from an OpenAPI spec.
   */
  public List<SecurityFinding> extractFindings(OpenAPI openApi) {
    if (openApi == null || openApi.getPaths() == null) {
      return Collections.emptyList();
    }

    List<SecurityFinding> findings = new ArrayList<>();

    // 1. Extract endpoint-level findings (public endpoints, accepted/returned schemas)
    findings.addAll(extractEndpointFindings(openApi));

    // 2. Extract schema-level findings (sensitive fields)
    findings.addAll(extractSchemaFindings(openApi));

    // 3. Extract dependency findings (schema references)
    findings.addAll(extractDependencyFindings(openApi));

    log.info("Extracted {} security findings from OpenAPI spec", findings.size());
    return findings;
  }

  /**
   * Extract findings related to endpoints: public access, request/response schemas.
   */
  private List<SecurityFinding> extractEndpointFindings(OpenAPI openApi) {
    List<SecurityFinding> findings = new ArrayList<>();

    openApi.getPaths().forEach((path, pathItem) -> {
      pathItem.readOperationsMap().forEach((method, operation) -> {
        String methodStr = method.name();

        // Check if endpoint is public (no security)
        if (!isOperationSecured(operation, openApi)) {
          findings.add(SecurityFinding.publicEndpoint(methodStr, path));
        }

        // Check request body (what this endpoint accepts)
        if (operation.getRequestBody() != null && operation.getRequestBody().getContent() != null) {
          operation.getRequestBody().getContent().forEach((mediaTypeStr, mediaType) -> {
            if (mediaType.getSchema() != null) {
              String schemaName = extractSchemaName(mediaType.getSchema());
              if (schemaName != null) {
                List<String> fields = extractSchemaFields(schemaName, openApi);
                findings.add(
                    SecurityFinding.endpointAcceptsSchema(methodStr, path, schemaName, fields));

                // Check if accepting sensitive fields
                fields.stream()
                    .filter(this::isSensitiveWord)
                    .forEach(field ->
                        findings.add(
                            SecurityFinding.writableSensitiveField(methodStr, path, schemaName,
                                field))
                    );
              }
            }
          });
        }

        // Check responses (what this endpoint returns)
        if (operation.getResponses() != null) {
          operation.getResponses().forEach((statusCode, response) -> {
            if (response.getContent() != null) {
              response.getContent().forEach((mediaTypeStr, mediaType) -> {
                if (mediaType.getSchema() != null) {
                  String schemaName = extractSchemaName(mediaType.getSchema());
                  if (schemaName != null) {
                    List<String> fields = extractSchemaFields(schemaName, openApi);
                    findings.add(
                        SecurityFinding.endpointReturnsSchema(methodStr, path, schemaName, fields));
                  }
                }
              });
            }
          });
        }
      });
    });

    return findings;
  }

  /**
   * Extract findings related to schemas: sensitive field detection.
   */
  private List<SecurityFinding> extractSchemaFindings(OpenAPI openApi) {
    List<SecurityFinding> findings = new ArrayList<>();

    if (openApi.getComponents() == null || openApi.getComponents().getSchemas() == null) {
      return findings;
    }

    openApi.getComponents().getSchemas().forEach((schemaName, schema) -> {
      if (schema.getProperties() != null) {
        schema.getProperties().forEach((fieldNameObj, fieldSchema) -> {
          String fieldName = String.valueOf(fieldNameObj);
          if (isSensitiveWord(fieldName)) {
            String fieldType = fieldSchema instanceof Schema ?
                ((Schema<?>) fieldSchema).getType() : "unknown";
            findings.add(SecurityFinding.schemaContainsSensitiveField(
                schemaName, fieldName, fieldType != null ? fieldType : "unknown"));
          }
        });
      }
    });

    return findings;
  }

  /**
   * Extract dependency findings: which schemas reference which other schemas.
   */
  private List<SecurityFinding> extractDependencyFindings(OpenAPI openApi) {
    List<SecurityFinding> findings = new ArrayList<>();

    if (openApi.getComponents() == null || openApi.getComponents().getSchemas() == null) {
      return findings;
    }

    openApi.getComponents().getSchemas().forEach((schemaName, schema) -> {
      Set<String> referencedSchemas = findReferencedSchemas(schema, new HashSet<>());
      referencedSchemas.forEach(refSchema ->
          findings.add(
              SecurityFinding.schemaDependency(schemaName, refSchema, "Schema: " + schemaName))
      );
    });

    return findings;
  }

  /**
   * Check if an operation is secured (has security requirements).
   */
  private boolean isOperationSecured(Operation operation, OpenAPI openApi) {
    if (operation.getSecurity() != null && !operation.getSecurity().isEmpty()) {
      return true;
    }
    // Check global security
    return openApi.getSecurity() != null && !openApi.getSecurity().isEmpty();
  }

  /**
   * Extract schema name from a Schema object (handles $ref).
   */
  private String extractSchemaName(Schema<?> schema) {
      if (schema == null) {
          return null;
      }

    if (schema.get$ref() != null) {
      String ref = schema.get$ref();
      if (ref.startsWith(COMPONENTS_SCHEMAS_PREFIX)) {
        return ref.substring(COMPONENTS_SCHEMAS_PREFIX.length());
      }
    }
    return null;
  }

  /**
   * Extract all field names from a schema.
   */
  private List<String> extractSchemaFields(String schemaName, OpenAPI openApi) {
    if (openApi.getComponents() == null || openApi.getComponents().getSchemas() == null) {
      return Collections.emptyList();
    }

    Schema<?> schema = openApi.getComponents().getSchemas().get(schemaName);
    if (schema == null || schema.getProperties() == null) {
      return Collections.emptyList();
    }

    // Convert Object keys to Strings
    List<String> fields = new ArrayList<>();
    schema.getProperties().keySet().forEach(key -> fields.add(String.valueOf(key)));
    return fields;
  }

  /**
   * Find all schemas referenced by a given schema (recursively).
   */
  private Set<String> findReferencedSchemas(Schema<?> schema, Set<String> visited) {
    Set<String> referenced = new HashSet<>();
      if (schema == null) {
          return referenced;
      }

    // Check $ref
    if (schema.get$ref() != null) {
      String schemaName = extractSchemaName(schema);
      if (schemaName != null && !visited.contains(schemaName)) {
        referenced.add(schemaName);
        visited.add(schemaName);
      }
    }

    // Check properties
    if (schema.getProperties() != null) {
      schema.getProperties().values().forEach(propSchema -> {
        if (propSchema != null) {
          referenced.addAll(findReferencedSchemas(propSchema, visited));
        }
      });
    }

    // Check array items
    if (schema.getItems() != null) {
      referenced.addAll(findReferencedSchemas(schema.getItems(), visited));
    }

    // Check allOf, anyOf, oneOf
    if (schema.getAllOf() != null) {
      schema.getAllOf().forEach(s -> referenced.addAll(findReferencedSchemas(s, visited)));
    }
    if (schema.getAnyOf() != null) {
      schema.getAnyOf().forEach(s -> referenced.addAll(findReferencedSchemas(s, visited)));
    }
    if (schema.getOneOf() != null) {
      schema.getOneOf().forEach(s -> referenced.addAll(findReferencedSchemas(s, visited)));
    }

    return referenced;
  }

  /**
   * Check if a word is considered sensitive.
   */
  private boolean isSensitiveWord(String text) {
      if (text == null) {
          return false;
      }
    String lower = text.toLowerCase(Locale.ROOT);
    return SENSITIVE_KEYWORDS.stream().anyMatch(lower::contains);
  }
}
