package io.github.sharmanish.schemasculpt.util;
<<<<<<<< HEAD:api/src/main/java/io/github/sharmanish/schemasculpt/util/OpenApiEnumFixer.java

import lombok.AccessLevel;
import lombok.NoArgsConstructor;
========
>>>>>>>> c2b2855 (changed package name, spotbug fixes):api/src/main/java/io/github/sharmanish/schemasculpt/util/OpenAPIEnumFixer.java

/**
 * Utility to fix uppercase enum values in OpenAPI JSON.
 *
 * <p>The Swagger parser stores enums as uppercase in the model objects, but the OpenAPI spec
 * requires lowercase values. This utility fixes the JSON after serialization.
 */
@NoArgsConstructor(access = AccessLevel.PRIVATE)
public class OpenApiEnumFixer {

  /**
   * Fix all uppercase enum values in OpenAPI JSON to their correct lowercase forms.
   *
   * @param json The OpenAPI JSON string with potentially uppercase enums
   * @return The fixed JSON with lowercase enum values
   */
  public static String fixEnums(String json) {
    if (json == null) {
      return null;
    }

    // Fix security scheme types
    json = json.replaceAll("\"type\"\\s*:\\s*\"OAUTH2\"", "\"type\": \"oauth2\"");
    json = json.replaceAll("\"type\"\\s*:\\s*\"APIKEY\"", "\"type\": \"apiKey\"");
    json = json.replaceAll("\"type\"\\s*:\\s*\"HTTP\"", "\"type\": \"http\"");
    json = json.replaceAll("\"type\"\\s*:\\s*\"OPENIDCONNECT\"", "\"type\": \"openIdConnect\"");
    json = json.replaceAll("\"type\"\\s*:\\s*\"MUTUALTLS\"", "\"type\": \"mutualTLS\"");

    // Fix parameter "in" locations
    json = json.replaceAll("\"in\"\\s*:\\s*\"QUERY\"", "\"in\": \"query\"");
    json = json.replaceAll("\"in\"\\s*:\\s*\"HEADER\"", "\"in\": \"header\"");
    json = json.replaceAll("\"in\"\\s*:\\s*\"PATH\"", "\"in\": \"path\"");
    json = json.replaceAll("\"in\"\\s*:\\s*\"COOKIE\"", "\"in\": \"cookie\"");

    // Fix parameter styles
    json = json.replaceAll("\"style\"\\s*:\\s*\"FORM\"", "\"style\": \"form\"");
    json = json.replaceAll("\"style\"\\s*:\\s*\"SIMPLE\"", "\"style\": \"simple\"");
    json = json.replaceAll("\"style\"\\s*:\\s*\"MATRIX\"", "\"style\": \"matrix\"");
    json = json.replaceAll("\"style\"\\s*:\\s*\"LABEL\"", "\"style\": \"label\"");
    json = json.replaceAll("\"style\"\\s*:\\s*\"SPACEDELIMITED\"", "\"style\": \"spaceDelimited\"");
    json = json.replaceAll("\"style\"\\s*:\\s*\"PIPEDELIMITED\"", "\"style\": \"pipeDelimited\"");
    json = json.replaceAll("\"style\"\\s*:\\s*\"DEEPOBJECT\"", "\"style\": \"deepObject\"");

    return json;
  }
}
