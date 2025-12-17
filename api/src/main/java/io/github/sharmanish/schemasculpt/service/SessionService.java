package io.github.sharmanish.schemasculpt.service;

import io.swagger.v3.oas.models.OpenAPI;

public interface SessionService {
  String createSession(String specText);

  void updateSessionSpec(String sessionId, String specText);

  void updateSessionSpec(String sessionId, OpenAPI openApi);

  OpenAPI getSpecForSession(String sessionId);

  String getSpecTextForSession(String sessionId);

  void closeSession(String sessionId);
}
