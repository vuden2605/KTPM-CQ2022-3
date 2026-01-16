package com.example.ingest_service.service;

import com.example.ingest_service. configure.StorageServiceWebClient;
import com.example.ingest_service. dto.request. Candle;
import jakarta.annotation.PostConstruct;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.java_websocket.client.WebSocketClient;
import org.java_websocket.handshake.ServerHandshake;
import org. springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import tools.jackson.databind.JsonNode;
import tools.jackson.databind. ObjectMapper;

import java.math.BigDecimal;
import java.net.URI;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.CompletableFuture;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
@Slf4j
public class BinanceService {
	private final RedisService redisService;
	private final CandleKafkaProducer kafkaService;
	private final ObjectMapper objectMapper = new ObjectMapper();
	private final BinanceRestService binanceRestService;
	private final StorageServiceWebClient storageServiceClient;

	@Value("${binance.ws.base-url}")
	private String baseUrl;

	private final List<String> symbols = List.of(
			"BTCUSDT",
			"ETHUSDT",
			"BNBUSDT",
			"XRPUSDT",
			"ADAUSDT"
	);

	private final List<String> intervals = List.of(
			"1m",
			"5m",
			"15m",
			"1h",
			"4h",
			"1d"
	);

	private String buildStreamUrl() {
		List<String> streams = new ArrayList<>();

		for (String s : symbols) {
			for (String i : intervals) {
				streams.add(s. toLowerCase() + "@kline_" + i);
			}
		}

		return baseUrl + "?streams=" + String.join("/", streams);
	}

	@PostConstruct
	public void startBinanceWebSocket() {
		String url = buildStreamUrl();
		WebSocketClient client = createClient(url);
		client.connect();
		log.info("WebSocket connecting to {}", url);

		CompletableFuture.runAsync(this::backfillOnStart)
				.exceptionally(ex -> {
					log.error("Backfill failed", ex);
					return null;
				});
	}

	private void backfillOnStart() {
		for (String symbol : symbols) {
			for (String interval : intervals) {
				try {
					Long lastOpenTime = storageServiceClient.getLastOpenTime(symbol, interval);
					long intervalMs = intervalToMillis(interval);
					long now = System.currentTimeMillis();
					long nowOpenTime = alignToInterval(now, intervalMs);

					List<Candle> candlesToBackfill = new ArrayList<>();

					if (lastOpenTime == null) {
						int limit = 1000;
						candlesToBackfill = binanceRestService.fetchLastClosedCandles(
								symbol, interval, limit
						);
						log.info("[Backfill] {} {} first time, fetched {} candles",
								symbol, interval, candlesToBackfill.size());
					} else {
						long missing = (nowOpenTime - lastOpenTime) / intervalMs;
						log.info("[Backfill] {} {}: lastOpenTime={}, nowOpenTime={}, missing={}",
								symbol, interval, lastOpenTime, nowOpenTime, missing);
						if (missing <= 0) {
							log.info("[Backfill] {} {}: no missing candles (lastOpenTime={}, nowOpenTime={})",
									symbol, interval, lastOpenTime, nowOpenTime);
						} else {
							int limit = (int) Math.min(missing, 1000);
							lastOpenTime += (missing - limit) * intervalMs;
							candlesToBackfill = binanceRestService.fetchClosedCandlesAfter(
									symbol, interval, lastOpenTime, limit
							);
							log.info("[Backfill] {} {}: missing={}, fetched={}",
									symbol, interval, missing, candlesToBackfill.size());
						}
					}

					if (!candlesToBackfill.isEmpty()) {
						for (Candle c : candlesToBackfill) {
							String candleJson = objectMapper.writeValueAsString(c);
							kafkaService.publishClosedCandle(symbol, interval, candleJson);
						}
						log.info("[Backfill] Published {} closed candles to Kafka:  {} {}",
								candlesToBackfill.size(), symbol, interval);
					}
				} catch (Exception e) {
					log.error("Error backfilling {} {}:  {}", symbol, interval, e. getMessage(), e);
				}
			}
		}
	}

	private WebSocketClient createClient(String url) {
		return new WebSocketClient(URI.create(url)) {

			@Override
			public void onOpen(ServerHandshake serverHandshake) {
				log.info("WebSocket connected to {}", url);
			}

			@Override
			public void onMessage(String message) {
				try {
					JsonNode node = objectMapper.readTree(message);
					JsonNode data = node.get("data");

					if (data != null) {
						String stream = node.get("stream").asText();
						String[] streamParts = stream.split("@");
						String symbol = streamParts[0].toUpperCase();
						String interval = streamParts[1]. substring(6);
						Candle candle = parseCandle(data, symbol, interval);

						if (candle != null) {
							String candleJson = objectMapper.writeValueAsString(candle);

							redisService.publishRealtimeCandle(symbol, interval, candleJson);

							if (Boolean.TRUE.equals(candle.getIsClosed())) {
								kafkaService.publishClosedCandle(symbol, interval, candleJson);
								log.debug("Published closed candle to Kafka: {} {} at {}",
										symbol, interval, candle.getOpenTime());
							}
						}
					}
				} catch (Exception e) {
					log. error("Error processing message", e);
				}
			}

			@Override
			public void onClose(int code, String reason, boolean remote) {
				log.info("WebSocket disconnected: code = {}, reason = {}, remote = {}", code, reason, remote);
			}

			@Override
			public void onError(Exception e) {
				log.error("WebSocket error", e);
			}
		};
	}

	private Candle parseCandle(JsonNode node, String symbol, String interval) {
		JsonNode k = node.path("k");
		if (k.isMissingNode()) return null;
		return Candle.builder()
				.symbol(symbol)
				.interval(interval)
				.openTime((k.path("t").asLong(0)))
				.closeTime((k.path("T").asLong(0)))
				.open(new BigDecimal(k.path("o").asText("0")))
				.high(new BigDecimal(k.path("h").asText("0")))
				.low(new BigDecimal(k.path("l").asText("0")))
				.close(new BigDecimal(k.path("c").asText("0")))
				.volume(new BigDecimal(k.path("v").asText("0")))
				.isClosed(k.path("x").asBoolean(false))
				.build();
	}

	private long intervalToMillis(String interval) {
		return switch (interval) {
			case "1m" -> 60_000L;
			case "5m" -> 5 * 60_000L;
			case "15m" -> 15 * 60_000L;
			case "1h" -> 60 * 60_000L;
			case "4h" -> 4 * 60 * 60_000L;
			case "1d" -> 24 * 60 * 60_000L;
			default -> throw new IllegalArgumentException("Unsupported interval " + interval);
		};
	}

	private long alignToInterval(long ts, long intervalMs) {
		return ts - (ts % intervalMs);
	}
}