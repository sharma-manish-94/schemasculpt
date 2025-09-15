package io.github.sharma_manish_94.schemasculpt_api.controller;

import io.github.sharma_manish_94.schemasculpt_api.dto.SpecEditRequest;
import io.github.sharma_manish_94.schemasculpt_api.service.SessionService;
import org.springframework.messaging.handler.annotation.MessageMapping;
import org.springframework.stereotype.Controller;

@Controller
public class WebSocketController {

    private final SessionService sessionService;

    public WebSocketController(final SessionService sessionService) {
        this.sessionService = sessionService;
    }

    @MessageMapping("/spec/edit")
    public void handleSpecEdit(SpecEditRequest message) {
        sessionService.updateSessionSpec(message.sessionId(), message.content());
    }
}
