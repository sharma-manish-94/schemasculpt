package io.github.sharma_manish_94.schemasculpt_api.service.impl;

import io.github.sharma_manish_94.schemasculpt_api.service.SessionService;
import io.github.sharma_manish_94.schemasculpt_api.service.SpecParsingService;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.parser.core.models.SwaggerParseResult;
import org.springframework.stereotype.Service;

import java.util.Map;
import java.util.Objects;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;

@Service
public class SessionServiceImpl implements SessionService {

    private final Map<String, OpenAPI> activeSessions = new ConcurrentHashMap<>();
    private final SpecParsingService specParsingService;

    public SessionServiceImpl(final SpecParsingService specParsingService) {
        this.specParsingService = specParsingService;
    }

    @Override
    public String createSession(final String specText) {

        final String sessionId = UUID.randomUUID().toString();
        final SwaggerParseResult parseResult = specParsingService.parse(specText);
        if (Objects.nonNull(parseResult)) {
            final OpenAPI openAPI = parseResult.getOpenAPI();
            if (Objects.nonNull(openAPI)) {
                activeSessions.put(sessionId, openAPI);
                return sessionId;
            } else {
                throw new IllegalArgumentException("Could not create session. Please check your spec");
            }
        }
        throw new IllegalArgumentException("Spec content is empty");
    }

    @Override
    public OpenAPI getSpecForSession(final String sessionId) {
        return activeSessions.getOrDefault(sessionId, null);
    }

    @Override
    public void closeSession(final String sessionId) {
        activeSessions.remove(sessionId);
    }
}
