package io.github.sharma_manish_94.schemasculpt_api.service.impl;

import io.github.sharma_manish_94.schemasculpt_api.service.SessionService;
import io.github.sharma_manish_94.schemasculpt_api.service.SpecParsingService;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.parser.core.models.SwaggerParseResult;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Service;

import java.time.Duration;
import java.util.Objects;
import java.util.UUID;

@Service
public class SessionServiceImpl implements SessionService {

    private final RedisTemplate<String, OpenAPI> redisTemplate;
    private final SpecParsingService specParsingService;

    public SessionServiceImpl(final SpecParsingService specParsingService,
                              final RedisTemplate<String, OpenAPI> redisTemplate) {
        this.specParsingService = specParsingService;
        this.redisTemplate = redisTemplate;
    }

    @Override
    public String createSession(final String specText) {

        final String sessionId = UUID.randomUUID().toString();
        final SwaggerParseResult parseResult = specParsingService.parse(specText);
        if (Objects.nonNull(parseResult)) {
            final OpenAPI openAPI = parseResult.getOpenAPI();
            if (Objects.nonNull(openAPI)) {
                redisTemplate.opsForValue().set(sessionId, openAPI, Duration.ofHours(1));
                return sessionId;
            } else {
                throw new IllegalArgumentException("Could not create session. Please check your spec");
            }
        }
        throw new IllegalArgumentException("Spec content is empty");
    }

    @Override
    public OpenAPI getSpecForSession(final String sessionId) {
        return redisTemplate.opsForValue().get(sessionId);
    }

    @Override
    public void closeSession(final String sessionId) {
        redisTemplate.delete(sessionId);
    }
}
