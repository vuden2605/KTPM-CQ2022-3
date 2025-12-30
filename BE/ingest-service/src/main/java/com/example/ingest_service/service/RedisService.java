package com.example.ingest_service.service;

import lombok.RequiredArgsConstructor;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class RedisService {
	private final StringRedisTemplate redisTemplate;
	private String key (String symbol, String interval) {
		return "candles:" + symbol + ":" + interval;
	}
	public void pushCandle(String symbol, String interval,  Long openTime, String candleJson) {
		String key = key(symbol, interval);
		redisTemplate.opsForZSet().add(key, candleJson, openTime);
		redisTemplate.opsForZSet().removeRange(key, 0, -1001);

	}
	public void publishCandle(String channel, String candleJson) {
		redisTemplate.convertAndSend(channel, candleJson);
	}
}
