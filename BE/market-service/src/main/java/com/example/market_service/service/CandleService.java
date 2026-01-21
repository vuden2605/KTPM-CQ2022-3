package com.example.market_service.service;

import com.example.market_service.Mapper.CandleMapper;
import com.example.market_service.dto.request.CandleCreationRequest;
import com.example.market_service.dto.response.CandleResponse;
import com.example.market_service.entity.Candle;
import com.example.market_service.repository.CandleRepository;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.transaction.Transactional;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.cache.annotation.CacheEvict;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.util.UriComponentsBuilder;

import java.math.BigDecimal;
import java.util.*;

@Service
@RequiredArgsConstructor
@Slf4j
public class CandleService {
	@Value("${binance.rest.base-url:https://api.binance.com/api/v3}")
	private String baseUrl;
	private final CandleRepository candleRepository;
	private final CandleMapper candleMapper;
	private final RedisTemplate<String, String> redisTemplate;
	private final ObjectMapper objectMapper;
	private final JdbcTemplate jdbcTemplate;
	private final RestTemplate restTemplate = new RestTemplate();

	public Long getLastOpenTime(String symbol, String interval) {
		return candleRepository.findLastOpenTime(symbol, interval);
	}

	public CandleResponse createCandle(CandleCreationRequest request) {
		Candle candle = candleMapper.toCandle(request);
		try {
			Candle savedCandle = candleRepository.saveAndFlush(candle);
			return candleMapper.toCandleResponse(savedCandle);
		} catch (Exception e) {
			log.debug(e.getMessage(), e);
			throw new RuntimeException(e);
		}
	}
	public void upsertCandle(
			String symbol,
			String interval,
			Long openTime,
			Long closeTime,
			BigDecimal open,
			BigDecimal high,
			BigDecimal low,
			BigDecimal close,
			BigDecimal volume
	) {
		candleRepository.upsertCandle(
				symbol,
				interval,
				openTime,
				closeTime,
				open,
				high,
				low,
				close,
				volume
		);
	}

	public List<Candle> getRecentCandles(
			String symbol,
			String interval,
			boolean isVip
	) {
		int limit = 1000;
		String key = "candles:" + symbol + ":" + interval;
		Long total = redisTemplate.opsForZSet().zCard(key);
		if (total == null || total == 0) {
			return getRecentCandlesFromDb(symbol, interval, limit);
		}
		long start = Math.max(0, total - limit);
		long end = total - 1;
		Set<String> raw = redisTemplate.opsForZSet()
				.range(key, start, end);
		if (raw == null || raw.isEmpty()) return getRecentCandlesFromDb(symbol, interval, limit);
		return raw.stream()
				.map(json -> {
					try {
						return objectMapper.readValue(json, Candle.class);
					} catch (JsonProcessingException e) {
						throw new RuntimeException(e);
					}
				})
				.toList();
	}
	public List<Candle> getRecentCandlesFromDb(
			String symbol,
			String interval,
			int limit
	) {
		Pageable pageable = PageRequest.of(0, limit);

		List<Candle> candles = candleRepository.findRecentCandles(symbol, interval, pageable);
		candles.sort(Comparator.comparingLong(Candle::getOpenTime));
		return candles;
	}
	public List<Candle> getCandlesBeforeOpenTime(
			String symbol,
			String interval,
			long openTime
	) {
		Pageable pageable = PageRequest.of(0, 500);

		return candleRepository
				.findBySymbolAndIntervalAndOpenTimeLessThanOrderByOpenTimeAsc(
						symbol,
						interval,
						openTime,
						pageable
				);
	}
	@Transactional
	public void batchInsert(List<Candle> candles) {
		String sql = """
        INSERT INTO candles
        (symbol,interval,open_time,close_time,open,high,low,close,volume)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT DO NOTHING
    """;

		jdbcTemplate.batchUpdate(sql, candles, 500,
				(ps, c) -> {
					ps.setString(1, c.getSymbol());
					ps.setString(2, c.getInterval());
					ps.setLong(3, c.getOpenTime());
					ps.setLong(4, c.getCloseTime());
					ps.setBigDecimal(5, c.getOpen());
					ps.setBigDecimal(6, c.getHigh());
					ps.setBigDecimal(7, c.getLow());
					ps.setBigDecimal(8, c.getClose());
					ps.setBigDecimal(9, c.getVolume());
				}
		);
	}
	public List<Candle> getCandlesBetweenOpenTimes(String symbol, String interval, long startTime, long endTime) {
		String url = UriComponentsBuilder
				.fromHttpUrl(baseUrl + "/klines")
				.queryParam("symbol", symbol)
				.queryParam("interval", interval)
				.queryParam("startTime", startTime)
				.queryParam("endTime", endTime)
				.toUriString();

		log.info("Calling Binance REST (last closed candles): {}", url);
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
	public Candle getLatestPrice(String symbol, String interval) {
		return candleRepository.findTopBySymbolAndIntervalOrderByOpenTimeDesc(symbol, interval)
				.orElseThrow(() -> new RuntimeException("Candle not found for " + symbol + " " + interval));
	}

}