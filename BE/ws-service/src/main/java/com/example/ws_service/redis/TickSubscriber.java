package com.example.ws_service.redis;
import com.example.ws_service.websocket.TickWebSockerHandler;
import lombok.extern.slf4j.Slf4j;
import org.jspecify.annotations.Nullable;
import org.springframework.data.redis.connection.Message;
import org.springframework.data.redis.connection.MessageListener;
import org.springframework.stereotype.Component;

@Component
@Slf4j
public class TickSubscriber implements MessageListener {
	private final TickWebSockerHandler wsHandler;
	public TickSubscriber(TickWebSockerHandler tickWebSockerHandler) {
		this.wsHandler = tickWebSockerHandler;

	}
	@Override
	public void onMessage(Message message, byte @Nullable [] pattern) {
		String wsTopic = new String(message.getChannel());
		String payload = new String(message.getBody());
		log.info("Received Redis message on topic {}: {}", wsTopic, payload);
		wsHandler.forward(wsTopic, payload);
	}
}

