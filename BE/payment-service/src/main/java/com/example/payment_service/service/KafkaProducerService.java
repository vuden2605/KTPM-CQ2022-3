package com.example.payment_service.service;

import com.example.payment_service.dto.event.VipUpgradeEvent;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.kafka.support.SendResult;
import org.springframework.stereotype.Service;

import java.util.concurrent.CompletableFuture;

@Service
@RequiredArgsConstructor
@Slf4j
public class KafkaProducerService {
	private final KafkaTemplate<String, VipUpgradeEvent> kafkaTemplate;

	@Value("${kafka.topics.vip-upgrade-events}")
	private String vipUpgradeTopic;

	public void publishVipUpgradeEvent(VipUpgradeEvent event) {
		log.info("📤 Publishing VIP upgrade event for userId: {}", event.getUserId());

		CompletableFuture<SendResult<String, VipUpgradeEvent>> future =
				kafkaTemplate.send(vipUpgradeTopic, event.getUserId().toString(), event);

		future.whenComplete((result, ex) -> {
			if (ex == null) {
				log.info("✅ VIP upgrade event published successfully");
				log.info("   └─ Topic: {}", result.getRecordMetadata().topic());
				log.info("   └─ Partition: {}", result.getRecordMetadata().partition());
				log.info("   └─ Offset: {}", result.getRecordMetadata().offset());
				log.info("   └─ UserId: {}", event.getUserId());
				log.info("   └─ Package: {} ({} days)", event.getVipPackageName(), event.getDurationDays());
			} else {
				log.error("❌ Failed to publish VIP upgrade event for userId: {}", event.getUserId(), ex);
			}
		});
	}
}