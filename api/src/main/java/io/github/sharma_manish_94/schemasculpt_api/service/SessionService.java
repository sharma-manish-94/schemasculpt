package io.github.sharma_manish_94.schemasculpt_api.service;

import io.swagger.v3.oas.models.OpenAPI;

public interface SessionService {
	String createSession(String specText);
	OpenAPI getSpecForSession(String sessionId);
	void closeSession(String sessionId);
}
