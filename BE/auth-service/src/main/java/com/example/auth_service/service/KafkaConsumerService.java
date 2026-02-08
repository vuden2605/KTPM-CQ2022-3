package com.example.auth_service.service;

import com.example.auth_service.dto.event.VipUpgradeEvent;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.kafka.support.KafkaHeaders;
import org.springframework.messaging.handler.annotation.Header;
import org.springframework.messaging.handler.annotation.Payload;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
@Slf4j
public class KafkaConsumerService {
	private final VipService vipService;

	@KafkaListener(
			topics = "${kafka.topics.vip-upgrade-events}",
			groupId = "${spring.kafka.consumer.group-id}",
			containerFactory = "kafkaListenerContainerFactory"
	)
	public void consumeVipUpgradeEvent(
			@Payload VipUpgradeEvent event,
			@Header(KafkaHeaders.RECEIVED_TOPIC) String topic,
			@Header(KafkaHeaders.RECEIVED_PARTITION) int partition,
			@Header(KafkaHeaders.OFFSET) long offset) {

		log.info("📥 Received VIP upgrade event");
		log.info("   └─ Topic: {}", topic);
		log.info("   └─ Partition: {}", partition);
		log.info("   └─ Offset: {}", offset);
		log.info("   └─ Event: {}", event);

		try {
			// ✅ Process event - Update User to VIP
			vipService.upgradeUserToVip(
					event.getUserId(),
					event.getDurationDays(),
					event.getVipPackageName()
			);

			log.info("✅ VIP upgrade event processed successfully for userId: {}", event.getUserId());

		} catch (Exception e) {
			log.error("❌ Failed to process VIP upgrade event for userId: {}", event.getUserId(), e);
			// TODO: Implement retry logic or dead letter queue
			throw e; // Re-throw để Kafka retry (nếu config)
		}
	}
}