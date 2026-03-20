package io.github.sharmanish.schemasculpt.controller;

import io.github.sharmanish.schemasculpt.dto.SpecEditRequest;
import io.github.sharmanish.schemasculpt.service.SessionService;
import io.github.sharmanish.schemasculpt.util.LogSanitizer;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.messaging.handler.annotation.MessageMapping;
import org.springframework.stereotype.Controller;

@Controller
public class WebSocketController {

  private static final Logger logger = LoggerFactory.getLogger(WebSocketController.class);
  private final SessionService sessionService;

  public WebSocketController(final SessionService sessionService) {
    this.sessionService = sessionService;
  }

  @MessageMapping("/spec/edit")
  public void handleSpecEdit(SpecEditRequest message) {
    try {
      if (message.sessionId() == null || message.sessionId().trim().isEmpty()) {
        logger.warn("Received spec edit request with null or empty sessionId");
        return;
      }

      if (message.content() == null || message.content().trim().isEmpty()) {
        logger.debug(
            "Received spec edit request with empty content for sessionId: {}",
            LogSanitizer.sanitize(message.sessionId()));
        return;
      }

      logger.debug(
          "Processing spec edit for sessionId: {}", LogSanitizer.sanitize(message.sessionId()));
      sessionService.updateSessionSpec(message.sessionId(), message.content());

    } catch (Exception e) {
      logger.error(
          "Unexpected error processing spec edit for sessionId: {}",
          LogSanitizer.sanitize(message.sessionId()),
          e);
      // Don't throw - this would disconnect the WebSocket
    }
  }
}
