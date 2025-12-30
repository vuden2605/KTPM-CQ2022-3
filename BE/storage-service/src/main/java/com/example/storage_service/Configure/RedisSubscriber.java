package com.example.storage_service.Configure;

import com.example.storage_service.dto.request.CandleCreationRequest;
import com.example.storage_service.entity.Candle;
import com.example.storage_service.service.CandleService;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.connection.Message;
import org.springframework.data.redis.connection.MessageListener;
import org.springframework.stereotype.Component;

@Component
@Slf4j
@RequiredArgsConstructor
public class RedisSubscriber implements MessageListener {
	private final CandleService candleService;
	private final ObjectMapper objectMapper;
	@Override
	public void onMessage(Message message, byte[] pattern) {
		try {
			String topic = new String(message.getChannel());
			String payload = new String(message.getBody());
			log.info("Received message on topic {}: {}", topic, payload);
			CandleCreationRequest request = objectMapper.readValue(payload, CandleCreationRequest.class);
			candleService.savedClosedCandle(request);
		}
		catch (Exception e) {
			log.error("Error processing message: {}", e.getMessage());
		}
	}
}
