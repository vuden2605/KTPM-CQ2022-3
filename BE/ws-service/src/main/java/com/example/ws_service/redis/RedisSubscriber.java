package com.example.ws_service.redis;

import com.example.ws_service.websocket.MarketWebSocketHandler;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.connection.Message;
import org.springframework.data.redis.connection.MessageListener;
import org.springframework.stereotype.Component;

@Component
@Slf4j
public class RedisSubscriber implements MessageListener {

	private final MarketWebSocketHandler wsHandler;

	public RedisSubscriber(MarketWebSocketHandler wsHandler) {
		this.wsHandler = wsHandler;
	}

	@Override
	public void onMessage(Message message, byte[] pattern) {
		String topic = new String(message.getChannel());
		String payload = new String(message.getBody());
		log.info("Received message on topic {}: {}", topic, payload);
		wsHandler.forward(topic, payload);
	}
}
