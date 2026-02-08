package com.example.auth_service.Configure;

import com.example.auth_service.dto.event.VipUpgradeEvent;
import org.apache.kafka.clients.consumer.ConsumerConfig;
import org.apache.kafka.common.serialization.StringDeserializer;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.kafka.config.ConcurrentKafkaListenerContainerFactory;
import org.springframework.kafka.core.ConsumerFactory;
import org.springframework.kafka.core.DefaultKafkaConsumerFactory;
import org.springframework.kafka.support.serializer.JsonDeserializer;

import java.util.HashMap;
import java.util.Map;

@Configuration
public class KafkaConsumerConfig {

	@Value("${spring.kafka.bootstrap-servers}")
	private String bootstrapServers;

	@Value("${spring.kafka.consumer.group-id}")
	private String groupId;

	@Bean
	public ConsumerFactory<String, VipUpgradeEvent> consumerFactory() {
		Map<String, Object> config = new HashMap<>();
		config.put(ConsumerConfig.BOOTSTRAP_SERVERS_CONFIG, bootstrapServers);
		config.put(ConsumerConfig.GROUP_ID_CONFIG, groupId);
		config.put(ConsumerConfig.KEY_DESERIALIZER_CLASS_CONFIG, StringDeserializer.class);
		config.put(ConsumerConfig.VALUE_DESERIALIZER_CLASS_CONFIG, JsonDeserializer.class);
		config.put(ConsumerConfig.AUTO_OFFSET_RESET_CONFIG, "earliest");
		config.put(JsonDeserializer.TRUSTED_PACKAGES, "*");
		config.put(JsonDeserializer.TYPE_MAPPINGS,
				"VipUpgradeEvent:com.example.auth_service.dto.event.VipUpgradeEvent");

		return new DefaultKafkaConsumerFactory<>(config,
				new StringDeserializer(),
				new JsonDeserializer<>(VipUpgradeEvent.class, false));
	}

	@Bean
	public ConcurrentKafkaListenerContainerFactory<String, VipUpgradeEvent>
	kafkaListenerContainerFactory() {
		ConcurrentKafkaListenerContainerFactory<String, VipUpgradeEvent> factory =
				new ConcurrentKafkaListenerContainerFactory<>();
		factory.setConsumerFactory(consumerFactory());
		return factory;
	}
}