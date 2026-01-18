package com.example.market_service.service;

import com.example.market_service.entity.Candle;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.apache.kafka.clients.consumer.ConsumerRecord;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.kafka.support.Acknowledgment;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Objects;

@Service
@RequiredArgsConstructor
@Slf4j
public class ClosedCandleConsumer {
	private final ObjectMapper objectMapper;
	private final CandleService candleService;
	private final RedisTemplate<String, String> redisTemplate;
	private static final int MAX_CANDLES = 1500;
	@KafkaListener(
			topics = "${kafka.topics.closed-candles}",
			groupId = "candle-redis-group",
			containerFactory = "kafkaListenerContainerFactory"
	)
	public void consumeRedis(
			List<ConsumerRecord<String, String>> records,
			Acknowledgment ack
	) {
		if (records.isEmpty()) return;

		try {
			for (ConsumerRecord<String, String> record : records) {
				Candle candle = objectMapper.readValue(record.value(), Candle.class);
				String redisKey = "candles:"
						+ candle.getSymbol() + ":"
						+ candle.getInterval();
				redisTemplate.opsForZSet().add(
						redisKey,
						record.value(),
						candle.getOpenTime()
				);

				Long setSize = redisTemplate.opsForZSet().size(redisKey);
				if (setSize != null && setSize > MAX_CANDLES) {
					long removeEnd = setSize - MAX_CANDLES - 1;
					redisTemplate.opsForZSet().removeRange(
							redisKey,
							0,
							removeEnd
					);
				}
			}
			ack.acknowledge();
		} catch (Exception e) {
			log.error("Failed to consume closed candles", e);
			throw new RuntimeException(e);
		}
	}
	@KafkaListener(
			topics = "${kafka.topics.closed-candles}",
			groupId = "candle-db-group",
			containerFactory = "kafkaListenerContainerFactory"
	)
	public void consumeDb(
			List<ConsumerRecord<String, String>> records,
			Acknowledgment ack
	) {
		if (records.isEmpty()) return;

		try {
			List<Candle> candles = records.stream().map(record -> {
				try {
					return objectMapper.readValue(record.value(), Candle.class);
				} catch (Exception e) {
					log.error("Failed to parse candle JSON: {}", record.value(), e);
					return null;
				}
			}).filter(Objects::nonNull).toList();
			candleService.batchInsert(candles);
			ack.acknowledge();
		} catch (Exception e) {
			log.error("Failed to consume closed candles", e);
			throw new RuntimeException(e);
		}
	}
}
