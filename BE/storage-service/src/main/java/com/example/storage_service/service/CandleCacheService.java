package com.example.storage_service.service;

import com.example.storage_service.dto.request.CandleCreationRequest;
import com.example.storage_service.entity.Candle;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.core.RedisCallback;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Service;

import java.util.List;

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
			Long size = redisTemplate.opsForZSet().zCard(key);
			if (size != null && size > MAX_CANDLES_IN_CACHE) {
				long removeCount = size - MAX_CANDLES_IN_CACHE;
				redisTemplate.opsForZSet().removeRange(key, 0, removeCount - 1);
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
}
