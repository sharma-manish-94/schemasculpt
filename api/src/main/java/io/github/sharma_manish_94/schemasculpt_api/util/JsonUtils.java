package io.github.sharma_manish_94.schemasculpt_api.util;

import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.Iterator;
import java.util.Map;
import lombok.extern.slf4j.Slf4j;

@Slf4j
public class JsonUtils {

  private static final ObjectMapper CLEAN_MAPPER = new ObjectMapper();

  static {
    CLEAN_MAPPER.setSerializationInclusion(JsonInclude.Include.NON_NULL);
    CLEAN_MAPPER.disable(SerializationFeature.FAIL_ON_EMPTY_BEANS);
    CLEAN_MAPPER.disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS);
  }

  /** Remove all null values from a JSON object recursively */
  public static Object removeNullValues(Object obj) {
    if (obj == null) {
      return null;
    }

    try {
      // Convert to JsonNode for manipulation
      JsonNode node = CLEAN_MAPPER.valueToTree(obj);
      JsonNode cleaned = removeNullNodes(node);

      // Convert back to Map if it was originally a Map-like object
      if (obj instanceof Map || obj.getClass().getSimpleName().contains("Schema")) {
        return CLEAN_MAPPER.convertValue(cleaned, Map.class);
      }

      return CLEAN_MAPPER.treeToValue(cleaned, obj.getClass());
    } catch (Exception e) {
      log.warn("Failed to clean null values from object: {}", e.getMessage());
      return obj;
    }
  }

  /** Recursively remove null nodes from JsonNode */
  private static JsonNode removeNullNodes(JsonNode node) {
    if (node.isObject()) {
      ObjectNode objectNode = (ObjectNode) node;
      ObjectNode result = objectNode.objectNode();

      Iterator<Map.Entry<String, JsonNode>> fields = objectNode.fields();
      while (fields.hasNext()) {
        Map.Entry<String, JsonNode> field = fields.next();
        JsonNode value = field.getValue();

        if (!value.isNull()) {
          result.set(field.getKey(), removeNullNodes(value));
        }
      }
      return result;
    } else if (node.isArray()) {
      for (int i = 0; i < node.size(); i++) {
        JsonNode element = node.get(i);
        if (element != null && !element.isNull()) {
          ((com.fasterxml.jackson.databind.node.ArrayNode) node).set(i, removeNullNodes(element));
        }
      }
    }

    return node;
  }

  /** Convert object to clean JSON string (no nulls) */
  public static String toCleanJson(Object obj) {
    try {
      Object cleaned = removeNullValues(obj);
      return CLEAN_MAPPER.writeValueAsString(cleaned);
    } catch (JsonProcessingException e) {
      log.error("Failed to serialize object to clean JSON", e);
      return "{}";
    }
  }

  /** Get the clean ObjectMapper instance */
  public static ObjectMapper getCleanMapper() {
    return CLEAN_MAPPER;
  }
}
