package com.example.storage_service.service;

import com.example.storage_service.dto.request.CandleCreationRequest;
import com.example.storage_service.entity.Candle;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.core.RedisCallback;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Service;

import java.time.Duration;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Set;

@Service
@RequiredArgsConstructor
@Slf4j
public class CandleCacheService {

	private final RedisTemplate<String, Object> redisTemplate;
	private final ObjectMapper objectMapper;

	private static final int MAX_CANDLES_IN_CACHE = 1000;

	private String getCacheKey(String symbol, String interval) {
		return String.format("candle:%s:%s" + ":closed", symbol, interval);
	}

	public void cacheCandle(Candle candle) {
		try {
			String key = getCacheKey(candle.getSymbol(), candle.getInterval());
			String json = objectMapper.writeValueAsString(candle);
			double score = candle.getOpenTime().doubleValue();

			redisTemplate.opsForZSet().add(key, json, score);
			redisTemplate.opsForZSet()
					.removeRange(key, 0, -MAX_CANDLES_IN_CACHE - 1);
			Long ttl = redisTemplate.getExpire(key);
			if (ttl < 0) {
				redisTemplate.expire(key, Duration.ofDays(2));
			}
		} catch (Exception e) {
			log.error("Error caching candle: {}", e.getMessage(), e);
		}
	}
	public void batchCacheCandles(String symbol, String interval, List<Candle> candles) {
		if (candles == null || candles.isEmpty()) return;

		String key = getCacheKey(symbol, interval);

		try {
			for (Candle c : candles) {
				try {
					String json = objectMapper.writeValueAsString(c);
					double score = c.getOpenTime().doubleValue();
					redisTemplate.opsForZSet().add(key, json, score);
				} catch (Exception e) {
					log.error("Error serializing candle: {}", e.getMessage());
				}
			}

			Long size = redisTemplate.opsForZSet().zCard(key);
			if (size != null && size > MAX_CANDLES_IN_CACHE) {
				long removeCount = size - MAX_CANDLES_IN_CACHE;
				redisTemplate.opsForZSet().removeRange(key, 0, removeCount - 1);
			}

			log.info("Batch cached {} candles for {} {}", candles.size(), symbol, interval);

		} catch (Exception e) {
			log.error("Error batch caching candles", e);
			throw new RuntimeException(e);
		}
	}
	public List<CandleCreationRequest> getRecentCandlesFromRedis(String symbol, String interval, int limit) {
		String key = getCacheKey(symbol, interval);

		Set<Object> rawSet = redisTemplate.opsForZSet()
				.reverseRange(key, 0, limit - 1);

		List<CandleCreationRequest> list = new ArrayList<>();
		if (rawSet == null || rawSet.isEmpty()) {
			return list;
		}

		for (Object obj : rawSet) {
			if (obj == null) continue;
			try {
				String json = obj.toString();
				CandleCreationRequest c = objectMapper.readValue(json, CandleCreationRequest.class);
				list.add(c);
			} catch (Exception e) {
				log.error("Error parsing candle json from Redis: {}", e.getMessage(), e);
			}
		}
		list.sort(Comparator.comparingLong(CandleCreationRequest::getOpenTime));
		return list;
	}

}
