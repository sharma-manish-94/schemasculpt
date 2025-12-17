package io.github.sharmanish.schemasculpt.controller;

import io.github.sharmanish.schemasculpt.dto.ProxyRequest;
import io.github.sharmanish.schemasculpt.dto.ProxyResponse;
import io.github.sharmanish.schemasculpt.service.proxy.ProxyService;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import reactor.core.publisher.Mono;

@RestController
@RequestMapping("/api/v1/proxy")
public class ProxyController {

  private final ProxyService proxyService;

  public ProxyController(ProxyService proxyService) {
    this.proxyService = proxyService;
  }

  @PostMapping("/request")
  public Mono<ResponseEntity<ProxyResponse>> forwardRequest(
      @Valid @RequestBody ProxyRequest request) {
    return proxyService.forwardRequest(request).map(ResponseEntity::ok);
  }
}
