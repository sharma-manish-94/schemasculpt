package io.github.sharma_manish_94.schemasculpt_api.service.impl;

import io.github.sharma_manish_94.schemasculpt_api.config.ApplicationConstants;
import io.github.sharma_manish_94.schemasculpt_api.exception.InvalidSpecificationException;
import io.github.sharma_manish_94.schemasculpt_api.exception.SessionNotFoundException;
import io.github.sharma_manish_94.schemasculpt_api.service.SessionService;
import io.github.sharma_manish_94.schemasculpt_api.service.SpecParsingService;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.parser.core.models.SwaggerParseResult;
import java.util.UUID;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@Transactional
@Slf4j
public class SessionServiceImpl implements SessionService {

  private final RedisTemplate<String, OpenAPI> redisTemplate;
  private final SpecParsingService specParsingService;

  public SessionServiceImpl(
      final SpecParsingService specParsingService,
      final RedisTemplate<String, OpenAPI> redisTemplate) {
    this.specParsingService = specParsingService;
    this.redisTemplate = redisTemplate;
  }

  @Override
  public String createSession(final String specText) {
    if (specText == null || specText.trim().isEmpty()) {
      throw new InvalidSpecificationException(ApplicationConstants.EMPTY_SPEC_MESSAGE);
    }

    final String sessionId = UUID.randomUUID().toString();
    log.debug("Creating session with ID: {}", sessionId);

    try {
      final SwaggerParseResult parseResult = specParsingService.parse(specText);
      if (parseResult == null) {
        throw new InvalidSpecificationException(ApplicationConstants.SPEC_PARSING_FAILED_MESSAGE);
      }

      final OpenAPI openAPI = parseResult.getOpenAPI();
      if (openAPI == null) {
        String errorMessage =
            parseResult.getMessages().isEmpty()
                ? ApplicationConstants.SPEC_PARSING_FAILED_MESSAGE
                : String.join(", ", parseResult.getMessages());
        throw new InvalidSpecificationException(errorMessage);
      }

      redisTemplate.opsForValue().set(sessionId, openAPI, ApplicationConstants.DEFAULT_SESSION_TTL);
      log.info("Successfully created session: {}", sessionId);
      return sessionId;

    } catch (Exception e) {
      log.error("Failed to create session: {}", e.getMessage(), e);
      if (e instanceof InvalidSpecificationException) {
        throw e;
      }
      throw new InvalidSpecificationException("Failed to create session: " + e.getMessage(), e);
    }
  }

  @Override
  public void updateSessionSpec(String sessionId, String specText) {
    if (sessionId == null || sessionId.trim().isEmpty()) {
      throw new IllegalArgumentException("Session ID cannot be null or empty");
    }

    if (specText == null || specText.trim().isEmpty()) {
      throw new InvalidSpecificationException(ApplicationConstants.EMPTY_SPEC_MESSAGE);
    }

    Boolean sessionExists = redisTemplate.hasKey(sessionId);
    if (Boolean.FALSE.equals(sessionExists)) {
      throw new SessionNotFoundException(sessionId);
    }

    try {
      log.debug("Updating session spec for session: {}", sessionId);
      SwaggerParseResult parseResult = specParsingService.parse(specText);

      if (parseResult == null) {
        throw new InvalidSpecificationException(ApplicationConstants.SPEC_PARSING_FAILED_MESSAGE);
      }

      OpenAPI openAPI = parseResult.getOpenAPI();
      if (openAPI == null) {
        String errorMessage =
            parseResult.getMessages().isEmpty()
                ? ApplicationConstants.SPEC_PARSING_FAILED_MESSAGE
                : String.join(", ", parseResult.getMessages());
        throw new InvalidSpecificationException(errorMessage);
      }

      redisTemplate.opsForValue().set(sessionId, openAPI, ApplicationConstants.DEFAULT_SESSION_TTL);
      log.debug("Successfully updated session spec for session: {}", sessionId);

    } catch (Exception e) {
      log.error("Failed to update session spec for session {}: {}", sessionId, e.getMessage(), e);
      if (e instanceof InvalidSpecificationException || e instanceof SessionNotFoundException) {
        throw e;
      }
      throw new InvalidSpecificationException(
          "Failed to update session spec: " + e.getMessage(), e);
    }
  }

  @Override
  public void updateSessionSpec(String sessionId, OpenAPI openApi) {
    if (sessionId == null || sessionId.trim().isEmpty()) {
      throw new IllegalArgumentException("Session ID cannot be null or empty");
    }

    if (openApi == null) {
      throw new InvalidSpecificationException("OpenAPI specification cannot be null");
    }

    Boolean sessionExists = redisTemplate.hasKey(sessionId);
    if (sessionExists == null || !sessionExists) {
      throw new SessionNotFoundException(sessionId);
    }

    try {
      log.debug("Updating session spec with OpenAPI object for session: {}", sessionId);
      redisTemplate.opsForValue().set(sessionId, openApi, ApplicationConstants.DEFAULT_SESSION_TTL);
      log.debug("Successfully updated session spec for session: {}", sessionId);
    } catch (Exception e) {
      log.error("Failed to update session spec for session {}: {}", sessionId, e.getMessage(), e);
      throw new InvalidSpecificationException(
          "Failed to update session spec: " + e.getMessage(), e);
    }
  }

  @Override
  @Transactional(readOnly = true)
  public OpenAPI getSpecForSession(final String sessionId) {
    if (sessionId == null || sessionId.trim().isEmpty()) {
      throw new IllegalArgumentException("Session ID cannot be null or empty");
    }

    log.debug("Retrieving spec for session: {}", sessionId);
    return redisTemplate.opsForValue().get(sessionId);
  }

  @Override
  public void closeSession(final String sessionId) {
    if (sessionId == null || sessionId.trim().isEmpty()) {
      throw new IllegalArgumentException("Session ID cannot be null or empty");
    }

    log.info("Closing session: {}", sessionId);
    Boolean deleted = redisTemplate.delete(sessionId);
    if (deleted.equals(Boolean.TRUE)) {
      log.info("Successfully closed session: {}", sessionId);
    } else {
      log.warn("Session {} was not found or already closed", sessionId);
    }
  }
}
