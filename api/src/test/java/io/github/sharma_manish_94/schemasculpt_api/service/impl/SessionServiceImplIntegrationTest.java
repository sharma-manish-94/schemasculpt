package io.github.sharma_manish_94.schemasculpt_api.service.impl;

import static org.assertj.core.api.Assertions.assertThat;

import io.github.sharma_manish_94.schemasculpt_api.service.SessionService;
import io.swagger.v3.oas.models.OpenAPI;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.testcontainers.containers.GenericContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;
import org.testcontainers.utility.DockerImageName;

@Testcontainers
@SpringBootTest
public class SessionServiceImplIntegrationTest {

  @Container
  static final GenericContainer<?> redis =
      new GenericContainer<>(DockerImageName.parse("redis:latest")).withExposedPorts(6379);

  @Autowired
  private SessionService sessionService;
  @Autowired
  private RedisTemplate<String, OpenAPI> redisTemplate;

  @DynamicPropertySource
  static void setProperties(DynamicPropertyRegistry registry) {
    registry.add("spring.data.redis.host", redis::getHost);
    registry.add("spring.data.redis.port", redis::getFirstMappedPort);
  }

  @Test
  void createSession_shouldStoreSpecInRedis() {
    String specText = "openapi: 3.0.0\ninfo:\n  title: Test API\n  version: 1.0.0\npaths: {}";

    String sessionId = sessionService.createSession(specText);

    assertThat(sessionId).isNotNull();

    OpenAPI storedSpec = redisTemplate.opsForValue().get(sessionId);
    assertThat(storedSpec).isNotNull();
    assertThat(storedSpec.getInfo().getTitle()).isEqualTo("Test API");
  }
}
