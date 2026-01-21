package com.example.ingest_service.service;

import com.example.ingest_service.configure.TradeProperties;
import com.example.ingest_service.dto.response.TickResponse;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.annotation.PostConstruct;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.java_websocket.client.WebSocketClient;
import org.java_websocket.handshake.ServerHandshake;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.net.URI;
import java.util.List;

@Service
@Slf4j
@RequiredArgsConstructor
public class BinanceTickService {
	@Value("${binance.ws.base-url}")
	private String baseUrl;

	private final TradeProperties tradeProperties;

	private final RedisService redisService;

	private final ObjectMapper objectMapper;

	private String buildTickStreamUrl() {
		List<String> streams = tradeProperties.getSymbols().stream()
				.map(s -> s.toLowerCase() + "@aggTrade")
				.toList();

		return baseUrl + "?streams=" + String.join("/", streams);
	}
	@PostConstruct
	public void start() {
		WebSocketClient tickClient = createClient(buildTickStreamUrl());
		tickClient.connect();
	}
	private WebSocketClient createClient(String url) {
		return new WebSocketClient(URI.create(url)) {
			@Override
			public void onOpen(ServerHandshake serverHandshake) {

			}

			@Override
			public void onMessage(String message) {
				TickResponse tickResponse;
				try {
					tickResponse = parseTickMessage(message);
				} catch (JsonProcessingException e) {
					throw new RuntimeException(e);
				}

				try {
					redisService.publicTicks(objectMapper.writeValueAsString(tickResponse));
				} catch (JsonProcessingException e) {
					throw new RuntimeException(e);
				}
			}

			@Override
			public void onClose(int i, String s, boolean b) {

			}

			@Override
			public void onError(Exception e) {

			}
		};
	}
	private TickResponse parseTickMessage(String message) throws JsonProcessingException {
		JsonNode node = objectMapper.readTree(message);
		String symbol = node.get("stream").asText().replace("@aggTrade", "").toUpperCase();
		JsonNode data = node.get("data");
		return TickResponse.builder()
				.symbol(symbol)
				.tradeId(data.get("a").asLong())
				.price(new BigDecimal(data.get("p").asText()))
				.volume(new BigDecimal(data.get("q").asText()))
				.eventTime(data.get("T").asLong())
				.maker(data.get("m").asBoolean())
				.build();
	}

}
