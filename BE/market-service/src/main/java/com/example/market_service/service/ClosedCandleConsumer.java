package com.example.market_service.service;

import com.example.market_service.entity.Candle;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.apache.kafka.clients.consumer.ConsumerRecord;
import org.springframework.data.redis.core.RedisCallback;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.kafka.support.Acknowledgment;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
@Slf4j
public class ClosedCandleConsumer {
	private final ObjectMapper objectMapper;
	private final CandleService candleService;
	private final RedisTemplate<String, String> redisTemplate;
	private static final int MAX_CANDLES = 1000;

	@KafkaListener(
			topics = "${kafka.topics.closed-candles}",
			groupId = "candle-processor-group",
			containerFactory = "kafkaListenerContainerFactory"
	)
	public void consume(
			List<ConsumerRecord<String, String>> records,
			Acknowledgment ack
	) {
		if (records.isEmpty()) return;

		List<Candle> candles = parseCandles(records);
		if (candles.isEmpty()) {
			ack.acknowledge();
			return;
		}

		try {
			processCandles(candles);
			ack.acknowledge();

			log.info("Successfully processed {} candles", candles.size());

		} catch (Exception e) {
			log.error("Failed to process candles batch, will retry", e);

		}
	}

	private void processCandles(List<Candle> candles) {

		List<Candle> savedCandles = candleService.batchInsertIdempotent(candles);

		Map<String, List<Candle>> groupedBySymbol = savedCandles.stream()
				.collect(Collectors.groupingBy(
						c -> c.getSymbol() + ":" + c.getInterval()
				));

		for (Map.Entry<String, List<Candle>> entry : groupedBySymbol.entrySet()) {
			updateRedisHotdata(entry.getKey(), entry.getValue());
		}
	}

	private void updateRedisHotdata(String key, List<Candle> candles) {
		String redisKey = "candles:" + key;

		try {
			// Add candles using pipeline
			redisTemplate.executePipelined((RedisCallback<Object>) connection -> {
				for (Candle candle : candles) {
					try {
						String json = objectMapper.writeValueAsString(candle);
						connection.zAdd(
								redisKey.getBytes(),
								candle.getOpenTime(),
								json.getBytes()
						);
					} catch (Exception e) {
						log.error("Failed to serialize candle", e);
					}
				}
				return null;
			});

			Long setSize = redisTemplate.opsForZSet().size(redisKey);
			if (setSize != null && setSize > MAX_CANDLES) {
				long removeEnd = setSize - MAX_CANDLES - 1;
				redisTemplate.opsForZSet().removeRange(redisKey, 0, removeEnd);
			}

		} catch (Exception e) {
			log.error("Failed to update Redis hotdata for key: {}", redisKey, e);
			throw e;
		}
	}

	private List<Candle> parseCandles(List<ConsumerRecord<String, String>> records) {
		return records.stream()
				.map(record -> {
					try {
						return objectMapper.readValue(record.value(), Candle.class);
					} catch (Exception e) {
						log.error("Failed to parse candle: {}", record.value(), e);
						sendToDLQ(record);
						return null;
					}
				})
				.filter(Objects::nonNull)
				.toList();
	}

	private void sendToDLQ(ConsumerRecord<String, String> record) {
		log.warn("Sent to DLQ: partition={}, offset={}",
				record.partition(), record.offset());
	}

}
