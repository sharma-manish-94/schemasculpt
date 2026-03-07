package io.github.sharmanish.schemasculpt.controller;

import io.github.sharmanish.schemasculpt.dto.request.SuggestFixRequest;
import io.github.sharmanish.schemasculpt.dto.response.SuggestFixResponse;
import jakarta.validation.Valid;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.reactive.function.client.WebClientResponseException;
import reactor.core.publisher.Mono;

@RestController
@RequestMapping("/api/v1/remediate")
@Slf4j
public class RemediationController {

  private static final String GENERIC_ERROR_MESSAGE =
      "Unable to generate fix suggestion. Please try again later.";

  private final WebClient webClient;

  public RemediationController(
      WebClient.Builder webClientBuilder, @Value("${ai.service.url}") String aiServiceUrl) {
    this.webClient = webClientBuilder.baseUrl(aiServiceUrl).build();
  }

  /**
   * Accepts a vulnerable code snippet and requests a fix from the AI service.
   *
   * @param request The request containing the code, language, and vulnerability type.
   * @return A Mono containing the suggested code fix.
   */
  @PostMapping("/suggest-fix")
  public Mono<ResponseEntity<SuggestFixResponse>> suggestFix(
      @RequestBody @Valid SuggestFixRequest request) {

    log.info("Requesting code fix for vulnerability type: {}", request.vulnerabilityType());

    return webClient
        .post()
        .uri("/ai/remediate/suggest-fix")
        .bodyValue(request)
        .retrieve()
        .bodyToMono(SuggestFixResponse.class)
        .map(ResponseEntity::ok)
        .onErrorResume(
            WebClientResponseException.class,
            error -> {
              log.error(
                  "AI service returned error status {} for vulnerability type '{}': {}",
                  error.getStatusCode(),
                  request.vulnerabilityType(),
                  error.getMessage());
              return Mono.just(
                  ResponseEntity.status(error.getStatusCode())
                      .body(new SuggestFixResponse(GENERIC_ERROR_MESSAGE)));
            })
        .onErrorResume(
            error -> {
              log.error(
                  "Failed to get fix suggestion from AI service for vulnerability type '{}': {}",
                  request.vulnerabilityType(),
                  error.getMessage(),
                  error);
              return Mono.just(
                  ResponseEntity.internalServerError()
                      .body(new SuggestFixResponse(GENERIC_ERROR_MESSAGE)));
            });
  }
}
