package com.example.storage_service.service;

import com.example.storage_service.entity.Candle;
import com.example.storage_service.repository.CandleRepository;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.apache.kafka.clients.consumer.ConsumerRecord;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.kafka.support.Acknowledgment;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;

@Service
@RequiredArgsConstructor
@Slf4j
public class ClosedCandleConsumer {
	private final ObjectMapper objectMapper;
	private final CandleService candleService;
	@KafkaListener(
			topics = "${kafka.topics.closed-candles}",
			containerFactory = "kafkaListenerContainerFactory"
	)
	public void consume(
			List<ConsumerRecord<String, String>> records,
			Acknowledgment ack
	) {
		if (records.isEmpty()) return;

		try {
			for (ConsumerRecord<String, String> record : records) {
				Candle candle = objectMapper.readValue(record.value(), Candle.class);
				candleService.upsertCandle(
						candle.getSymbol(),
						candle.getInterval(),
						candle.getOpenTime(),
						candle.getCloseTime(),
						candle.getOpen(),
						candle.getHigh(),
						candle.getLow(),
						candle.getClose(),
						candle.getVolume()
				);
			}
			ack.acknowledge();
		} catch (Exception e) {
			log.error("Failed to consume closed candles", e);
		}
	}
}
