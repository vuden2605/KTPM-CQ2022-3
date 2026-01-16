package com.example.ingest_service.service;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
@Slf4j
public class RedisService {
	private final StringRedisTemplate redisTemplate;
	public void publishRealtimeCandle(String symbol, String interval, String candleJson) {
		String channel = String.format("candle:%s:%s:realtime", symbol, interval);
		redisTemplate.convertAndSend(channel, candleJson);
		log.info("Published realtime candle to Redis: {}", channel);
	}
}
