package io.github.sharmanish.schemasculpt.config;

import io.swagger.v3.oas.models.OpenAPI;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.redis.connection.RedisConnectionFactory;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.data.redis.serializer.GenericJacksonJsonRedisSerializer;
import org.springframework.data.redis.serializer.StringRedisSerializer;
import tools.jackson.databind.DefaultTyping;
import tools.jackson.databind.json.JsonMapper;
import tools.jackson.databind.jsontype.BasicPolymorphicTypeValidator;

/**
 * Configuration class for setting up Redis integration.
 *
 * <p>Defines a {@link RedisTemplate} bean for storing and retrieving {@link OpenAPI} objects in
 * Redis, using JSON serialization for values and string serialization for keys.
 */
@Configuration
public class RedisConfig {

  /**
   * Creates a {@link RedisTemplate} for {@link OpenAPI} objects.
   *
   * @param connectionFactory the Redis connection factory
   * @return a configured {@link RedisTemplate} for String keys and OpenAPI values
   */
  @Bean
  public RedisTemplate<String, OpenAPI> redisTemplate(RedisConnectionFactory connectionFactory,
                                                      JsonMapper jsonMapper) {
    RedisTemplate<String, OpenAPI> template = new RedisTemplate<>();
    template.setConnectionFactory(connectionFactory);
    template.setKeySerializer(new StringRedisSerializer());

    JsonMapper redisMapper = jsonMapper.rebuild()
            .activateDefaultTyping(
                    BasicPolymorphicTypeValidator.builder()
                            .allowIfBaseType(Object.class)
                            .build(),
                    DefaultTyping.NON_FINAL
            )
            .build();

    template.setValueSerializer(new GenericJacksonJsonRedisSerializer(redisMapper));
    return template;
  }
}
