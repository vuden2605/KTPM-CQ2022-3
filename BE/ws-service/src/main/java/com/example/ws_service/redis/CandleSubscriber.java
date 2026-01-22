package com.example.ws_service.redis;

import com.example.ws_service.websocket.CandleBroadcast;
import com.example.ws_service.websocket.CandleWebSocketController;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.connection.Message;
import org.springframework.data.redis.connection.MessageListener;
import org.springframework.stereotype.Component;

@Component
@Slf4j
@RequiredArgsConstructor
public class CandleSubscriber implements MessageListener {
	private final CandleBroadcast wsHandler;

	@Override
	public void onMessage(Message message, byte[] pattern) {
		String redisTopic = new String(message.getChannel());
		String payload = new String(message.getBody());

		String[] parts = redisTopic.split(":");
		if (parts.length < 4) return;

		String symbol = parts[1];
		String interval = parts[2];

		wsHandler.broadcast(symbol, interval, payload);;
	}
}
