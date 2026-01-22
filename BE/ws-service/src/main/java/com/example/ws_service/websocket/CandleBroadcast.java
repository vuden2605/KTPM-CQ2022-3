package com.example.ws_service.websocket;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
@Slf4j
public class CandleBroadcast {
	private final SimpMessagingTemplate messagingTemplate;

	public void broadcast(String symbol, String interval,  String payload) {
		String destination = "/topic/candle." + symbol + "." + interval;

		try {
			messagingTemplate.convertAndSend(destination, payload);
			log.debug("Sent message to {}", destination);
		} catch (Exception e) {
			log.error("Failed to broadcast to {}", destination, e);
		}
	}
}
