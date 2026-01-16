package com.example.ingest_service.service;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.kafka.support.SendResult;
import org.springframework.stereotype.Service;
import java.util.List;
import java.util.concurrent.CompletableFuture;

@Service
@RequiredArgsConstructor
@Slf4j
public class CandleKafkaProducer {
	private final KafkaTemplate<String, String> kafkaTemplate;

	@Value("${kafka.topics.closed-candles}")
	private String closedCandlesTopic;

	public void publishClosedCandle(String symbol, String interval, String candleJson) {
		String key = String.format("%s:%s", symbol, interval);

		try {
			CompletableFuture<SendResult<String, String>> future =
					kafkaTemplate.send(closedCandlesTopic, key, candleJson);

			future.whenComplete((result, ex) -> {
				if (ex != null) {
					log.error("Failed to send message for {}:{} to topic {}",
							symbol, interval, closedCandlesTopic, ex);
				} else {
					log.debug("Successfully sent message for {}:{} to partition {} with offset {}",
							symbol, interval,
							result.getRecordMetadata().partition(),
							result.getRecordMetadata().offset());
				}
			});
		} catch (Exception e) {
			log.error("Unexpected error when sending Kafka message for {}:{}",
					symbol, interval, e);
		}
	}
}