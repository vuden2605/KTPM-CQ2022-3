package com.example.ws_service.websocket;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

@Component
@Slf4j
public class CandleWebSocketHandler extends  AbstractTopicWebSocketHandler {

	public CandleWebSocketHandler(ObjectMapper objectMapper) {
		super(objectMapper);
	}

	@Override
	protected String resolveTopic(JsonNode node) {
		return "candle:%s:%s".formatted(
				node.get("symbol").asText(),
				node.get("interval").asText()
		);
	}
}
