package io.github.sharmanish.schemasculpt.config;

import io.netty.channel.ChannelOption;
import io.netty.handler.timeout.ReadTimeoutHandler;
import io.netty.handler.timeout.WriteTimeoutHandler;
import java.time.Duration;
import java.util.concurrent.TimeUnit;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.client.reactive.ReactorClientHttpConnector;
import org.springframework.http.codec.json.JacksonJsonDecoder;
import org.springframework.http.codec.json.JacksonJsonEncoder;
import org.springframework.web.reactive.function.client.ExchangeStrategies;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.netty.http.client.HttpClient;
import tools.jackson.databind.json.JsonMapper;

@Configuration
public class WebClientConfig {

  @Bean
  public WebClient.Builder webClientBuilder(JsonMapper jsonMapper) {
    // Configure HttpClient with proper timeouts and connection settings
    // Increased timeouts for AI operations which can take longer with local LLMs
    HttpClient httpClient =
        HttpClient.create()
            .option(ChannelOption.CONNECT_TIMEOUT_MILLIS, 30000) // 30 seconds connection timeout
            .responseTimeout(Duration.ofSeconds(300)) // 5 minutes response timeout
            .doOnConnected(
                conn ->
                    conn.addHandlerLast(new ReadTimeoutHandler(300, TimeUnit.SECONDS))
                        .addHandlerLast(new WriteTimeoutHandler(300, TimeUnit.SECONDS)));

    // Configure ExchangeStrategies to use our custom ObjectMapper and increase buffer size
    ExchangeStrategies strategies =
        ExchangeStrategies.builder()
            .codecs(
                configurer -> {
                  // Increase buffer size to 10MB to handle large OpenAPI specs
                  configurer.defaultCodecs().maxInMemorySize(10 * 1024 * 1024);

                  configurer.defaultCodecs().jacksonJsonEncoder(new JacksonJsonEncoder(jsonMapper));
                  configurer.defaultCodecs().jacksonJsonDecoder(new JacksonJsonDecoder(jsonMapper));
                })
            .build();

    return WebClient.builder()
        .clientConnector(new ReactorClientHttpConnector(httpClient))
        .exchangeStrategies(strategies);
  }
}
