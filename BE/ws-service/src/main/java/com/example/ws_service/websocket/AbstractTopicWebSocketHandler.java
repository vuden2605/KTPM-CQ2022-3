package com.example.ws_service.websocket;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.socket.CloseStatus;
import org.springframework.web.socket.TextMessage;
import org.springframework.web.socket.WebSocketSession;
import org.springframework.web.socket.handler.TextWebSocketHandler;

import java.util.ArrayList;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

@Slf4j
@RequiredArgsConstructor
public abstract class AbstractTopicWebSocketHandler
		extends TextWebSocketHandler {

	protected final ObjectMapper objectMapper;


	protected final Map<String, Set<WebSocketSession>> topicSubscribers = new ConcurrentHashMap<>();
	protected final Map<String, Set<String>> sessionTopics = new ConcurrentHashMap<>();

	protected final ExecutorService executor =
			Executors.newVirtualThreadPerTaskExecutor();

	@Override
	public void afterConnectionEstablished(WebSocketSession session) {
		log.info("WS connected: {}", session.getId());
		sessionTopics.put(session.getId(), ConcurrentHashMap.newKeySet());
	}

	@Override
	protected void handleTextMessage(WebSocketSession session, TextMessage message)
			throws Exception {

		JsonNode node = objectMapper.readTree(message.getPayload());
		if (!"SUBSCRIBE".equals(node.get("type").asText())) return;

		String topic = resolveTopic(node);
		sessionTopics.get(session.getId()).add(topic);

		topicSubscribers
				.computeIfAbsent(topic, k -> ConcurrentHashMap.newKeySet())
				.add(session);

		log.info("Session {} subscribed {}", session.getId(), topic);
	}

	protected abstract String resolveTopic(JsonNode node);

	@Override
	public void afterConnectionClosed(WebSocketSession session, CloseStatus status) {
		Set<String> topics = sessionTopics.remove(session.getId());
		if (topics != null) {
			topics.forEach(topic -> {
				Set<WebSocketSession> subs = topicSubscribers.get(topic);
				if (subs != null) {
					subs.remove(session);
					if (subs.isEmpty()) topicSubscribers.remove(topic);
				}
			});
		}
		log.info("WS disconnected: {}", session.getId());
	}

	public void forward(String topic, String payload) {
		Set<WebSocketSession> subs = topicSubscribers.get(topic);
		if (subs == null || subs.isEmpty()) return;

		TextMessage message = new TextMessage(payload);
		for (WebSocketSession session : new ArrayList<>(subs)) {
			executor.submit(() -> send(session, topic, message));
		}
	}

	private void send(WebSocketSession session, String topic, TextMessage message) {
		try {
			if (session.isOpen()) {
				session.sendMessage(message);
			} else {
				remove(topic, session);
			}
		} catch (Exception e) {
			log.error("WS send error {}", session.getId(), e);
			remove(topic, session);
		}
	}

	private void remove(String topic, WebSocketSession session) {
		Set<WebSocketSession> subs = topicSubscribers.get(topic);
		if (subs != null) subs.remove(session);
	}
}

