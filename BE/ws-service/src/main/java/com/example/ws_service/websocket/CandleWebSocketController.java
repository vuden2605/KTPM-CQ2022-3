package com.example.ws_service.websocket;

import lombok.RequiredArgsConstructor;
import org.springframework.messaging.handler.annotation.MessageMapping;
import org.springframework.stereotype.Controller;

@Controller
@RequiredArgsConstructor
public class CandleWebSocketController {

	@MessageMapping("/subscribe")
	public void subscribe() {

	}
}
