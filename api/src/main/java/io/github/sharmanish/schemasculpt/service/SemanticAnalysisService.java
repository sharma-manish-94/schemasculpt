package io.github.sharmanish.schemasculpt.service;

import static io.github.sharmanish.schemasculpt.service.SchemaDiffService.SCHEMA_NAME;

import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.media.Schema;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import lombok.Builder;
import lombok.Data;
import org.apache.commons.text.similarity.CosineSimilarity;
import org.springframework.stereotype.Service;

@Service
public class SemanticAnalysisService {

  public SemanticReport analyzeSemantics(OpenAPI openApi) {
    SemanticReport semanticReport = new SemanticReport();
    if (openApi.getComponents() == null || openApi.getComponents().getSchemas() == null) {
      return semanticReport;
    }
    openApi
        .getComponents()
        .getSchemas()
        .forEach(
            (schemaName, schema) -> {
              if (schema.getProperties() != null) {
                schema
                    .getProperties()
                    .forEach(
                        (propertyName, propertyValue) -> {
                          String description = ((Schema) propertyValue).getDescription();
                          if (description != null && !description.isEmpty()) {
                            double score =
                                this.calculateRelevance((String) propertyName, description);
                            if (score < 0.1) {
                              semanticReport.addIssue(
                                  schemaName, (String) propertyName, description, score);
                            }
                          }
                        });
              }
            });
    return semanticReport;
  }

  /**
   * Calculates similarity between a Property Name (e.g., "creationDate") and its Description (e.g.,
   * "The date when the user was created").
   */
  private double calculateRelevance(String propName, String description) {
    // 1. Normalize: "creationDate" -> "creation date"
    String normalizedName = splitCamelCase(propName).toLowerCase();
    String normalizedDesc = description.toLowerCase();

    // 2. Tokenize
    Map<CharSequence, Integer> nameVector = tokenize(normalizedName);
    Map<CharSequence, Integer> descVector = tokenize(normalizedDesc);

    // 3. Cosine Similarity
    CosineSimilarity cosine = new CosineSimilarity();
    return cosine.cosineSimilarity(nameVector, descVector);
  }

  // Helper: "camelCase" -> "camel case"
  private String splitCamelCase(String s) {
    return s.replaceAll(
        String.format(
            "%s|%s|%s",
            "(?<=[A-Z])(?=[A-Z][a-z])", "(?<=[^A-Z])(?=[A-Z])", "(?<=[A-Za-z])(?=[^A-Za-z])"),
        " ");
  }

  // Helper: Turn string into Frequency Map (Bag of Words)
  private Map<CharSequence, Integer> tokenize(String text) {
    Map<CharSequence, Integer> map = new HashMap<>();
    String[] words = text.split("\\W+"); // Split by non-word characters
    for (String word : words) {
      if (word.length() > 2) { // Ignore tiny words like "is", "at"
        map.merge(word, 1, Integer::sum);
      }
    }
    return map;
  }

  @Data
  public static class SemanticReport {
    private List<SemanticIssue> issues = new ArrayList<>();

    public void addIssue(String schema, String field, String desc, double score) {
      issues.add(
          SemanticIssue.builder()
              .location(SCHEMA_NAME + schema + " -> " + field)
              .fieldDescription(desc)
              .relevanceScore(score)
              .suggestion(
                  "Field name words do not appear in description. Is this"
                      + " description accurate")
              .build());
    }
  }

  @Data
  @Builder
  public static class SemanticIssue {
    private String location;
    private String fieldDescription;
    private double relevanceScore;
    private String suggestion;
  }
}
