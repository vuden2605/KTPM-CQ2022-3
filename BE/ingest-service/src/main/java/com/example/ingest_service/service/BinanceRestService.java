package com.example.ingest_service.service;

import com.example.ingest_service.dto.request.Candle;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.util.UriComponentsBuilder;
import tools.jackson.databind.JsonNode;
import tools.jackson.databind.ObjectMapper;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.List;

@Service
@RequiredArgsConstructor
@Slf4j
public class BinanceRestService {
	private final RestTemplate restTemplate = new RestTemplate();
	private final ObjectMapper objectMapper = new ObjectMapper();

	@Value("${binance.rest.base-url:https://api.binance.com/api/v3}")
	private String baseUrl;

	public List<Candle> fetchLastClosedCandles(String symbol, String interval, int limit) {
		String url = UriComponentsBuilder
				.fromHttpUrl(baseUrl + "/klines")
				.queryParam("symbol", symbol)
				.queryParam("interval", interval)
				.queryParam("limit", limit)
				.toUriString();

		log.info("Calling Binance REST (last closed candles): {}", url);
		return callKlinesApi(url, symbol, interval);
	}

	public List<Candle> fetchClosedCandlesAfter(String symbol, String interval, long lastOpenTime, int limit) {
		long intervalMs = intervalToMillis(interval);
		long startTime = lastOpenTime + intervalMs;

		String url = UriComponentsBuilder
				.fromHttpUrl(baseUrl + "/klines")
				.queryParam("symbol", symbol)
				.queryParam("interval", interval)
				.queryParam("startTime", startTime)
				.queryParam("limit", limit)
				.toUriString();

		log.info("Calling Binance REST (closed candles after lastOpenTime={}): {}", lastOpenTime, url);
		return callKlinesApi(url, symbol, interval);
	}

	private List<Candle> callKlinesApi(String url, String symbol, String interval) {
		try {
			String raw = restTemplate.getForObject(url, String.class);
			JsonNode arr = objectMapper.readTree(raw);
			List<Candle> result = new ArrayList<>();

			if (!arr.isArray()) {
				log.warn("Unexpected klines response for {} {}: {}", symbol, interval, raw);
				return result;
			}

			for (JsonNode k : arr) {
				long openTime = k.get(0).asLong();
				String o = k.get(1).asText();
				String h = k.get(2).asText();
				String l = k.get(3).asText();
				String c = k.get(4).asText();
				String v = k.get(5).asText();
				long closeTime = k.get(6).asLong();

				Candle candle = Candle.builder()
						.symbol(symbol)
						.interval(interval)
						.openTime(openTime)
						.closeTime(closeTime)
						.open(new BigDecimal(o))
						.high(new BigDecimal(h))
						.low(new BigDecimal(l))
						.close(new BigDecimal(c))
						.volume(new BigDecimal(v))
						.build();
				result.add(candle);
			}

			log.info("Fetched {} klines from REST for {} {}", result.size(), symbol, interval);
			return result;
		} catch (Exception e) {
			log.error("Error fetching klines from Binance for {} {}: {}", symbol, interval, e.getMessage(), e);
			return List.of();
		}
	}

	private long intervalToMillis(String interval) {
		return switch (interval) {
			case "1m"  -> 60_000L;
			case "3m"  -> 3 * 60_000L;
			case "5m"  -> 5 * 60_000L;
			case "15m" -> 15 * 60_000L;
			case "30m" -> 30 * 60_000L;
			case "1h"  -> 60 * 60_000L;
			case "2h"  -> 2 * 60 * 60_000L;
			case "4h"  -> 4 * 60 * 60_000L;
			case "6h"  -> 6 * 60 * 60_000L;
			case "8h"  -> 8 * 60 * 60_000L;
			case "12h" -> 12 * 60 * 60_000L;
			case "1d"  -> 24 * 60 * 60_000L;
			case "3d"  -> 3 * 24 * 60 * 60_000L;
			case "1w"  -> 7 * 24 * 60 * 60_000L;
			case "1M"  -> 30L * 24 * 60 * 60_000L;
			default    -> throw new IllegalArgumentException("Unsupported interval " + interval);
		};
	}
}