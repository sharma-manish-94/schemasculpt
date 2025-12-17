package io.github.sharmanish.schemasculpt.service.proxy;

import io.github.sharmanish.schemasculpt.dto.ProxyRequest;
import io.github.sharmanish.schemasculpt.dto.ProxyResponse;
import java.net.URI;
import java.net.URISyntaxException;
import java.util.List;
import java.util.Map;
import org.springframework.http.HttpMethod;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.ClientResponse;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

@Service
public class ProxyService {

  private static final List<String> ALLOWED_HOSTS = List.of("localhost", "127.0.0.1");
  private final WebClient webClient;

  public ProxyService(WebClient.Builder webClientBuilder) {
    this.webClient = webClientBuilder.build();
  }

  public Mono<ProxyResponse> forwardRequest(ProxyRequest request) {
    this.validateUrl(request.url());
    return webClient
        .method(HttpMethod.valueOf(request.method().toUpperCase()))
        .uri(request.url())
        .headers(headers -> headers.setAll(request.headers()))
        .bodyValue(request.body() != null ? request.body() : "")
        .exchangeToMono(this::handleResponse);
  }

  private void validateUrl(String url) {
    try {
      URI uri = new URI(url);
      if (!ALLOWED_HOSTS.contains(uri.getHost())) {
        throw new SecurityException("Host not allowed: " + uri.getHost());
      }
    } catch (URISyntaxException e) {
      throw new IllegalArgumentException("Invalid URL format", e);
    }
  }

  private Mono<ProxyResponse> handleResponse(ClientResponse clientResponse) {
    return clientResponse
        .bodyToMono(Object.class)
        .defaultIfEmpty("")
        .map(
            body -> {
              Map<String, String> headers =
                  clientResponse.headers().asHttpHeaders().toSingleValueMap();
              return new ProxyResponse(clientResponse.statusCode().value(), headers, body);
            });
  }
}
