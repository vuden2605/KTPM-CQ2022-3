package com.example.ws_service.websocket;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;
import org.springframework.web.socket.CloseStatus;
import org.springframework.web.socket.TextMessage;
import org.springframework.web.socket.WebSocketSession;
import org.springframework.web.socket.handler.TextWebSocketHandler;

import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

@Component
@Slf4j
public class MarketWebSocketHandler extends TextWebSocketHandler {

	private static final ObjectMapper objectMapper = new ObjectMapper();

	private final Map<String, Set<WebSocketSession>> topicSubscribers = new ConcurrentHashMap<>();

	private final Map<String, Set<String>> sessionTopics = new ConcurrentHashMap<>();

	ExecutorService executor = Executors.newVirtualThreadPerTaskExecutor();

	@Override
	public void afterConnectionEstablished(WebSocketSession session) {
		log.info("WS connected: {}", session.getId());
		sessionTopics.put(session.getId(), ConcurrentHashMap.newKeySet());
	}
	@Override
	protected void handleTextMessage(WebSocketSession session, TextMessage message) throws JsonProcessingException {
		JsonNode node = objectMapper.readTree(message.getPayload());

		if ("SUBSCRIBE".equals(node.get("type").asText())) {
			String topic = "candle:%s:%s".formatted(
					node.get("symbol").asText(),
					node.get("interval").asText()
			);
			sessionTopics.get(session.getId()).add(topic);
			topicSubscribers
					.computeIfAbsent(topic, k -> ConcurrentHashMap.newKeySet())
					.add(session);

			log.info("Session {} subscribed {}", session.getId(), topic);
		}
	}
	@Override
	public void afterConnectionClosed(WebSocketSession session, CloseStatus status) {
		Set<String> topics = sessionTopics.remove(session.getId());

		if (topics != null) {
			for (String topic : topics) {
				Set<WebSocketSession> subs = topicSubscribers.get(topic);
				if (subs != null) {
					subs.remove(session);
					if (subs.isEmpty()) {
						topicSubscribers.remove(topic);
					}
				}
			}
		}

		log.info("WS disconnected: {}", session.getId());
	}

	public void forward(String topic, String payload) {

		Set<WebSocketSession> subs = topicSubscribers.get(topic);
		if (subs == null || subs.isEmpty()) return;
		TextMessage message = new TextMessage(payload);
		List<WebSocketSession> snapshot = new ArrayList<>(subs);
		for (WebSocketSession session : snapshot) {
			executor. submit(() -> {
				try {
					if (session.isOpen()) {
						log.info("Send to session {}: {}", session.getId(), payload);
						session.sendMessage(message);
					} else {
						removeSubscriber(topic, session);
					}
				} catch (Exception e) {
					log.error("WS send error to session {}:  {}", session.getId(), e.getMessage());
					removeSubscriber(topic, session);
				}
			});
		}
	}
	private void removeSubscriber(String topic, WebSocketSession session) {
		Set<WebSocketSession> subs = topicSubscribers. get(topic);
		if (subs != null) {
			subs.remove(session);
		}
	}
}
