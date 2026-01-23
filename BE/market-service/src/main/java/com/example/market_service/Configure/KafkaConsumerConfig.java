package com.example.market_service.Configure;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.kafka.config.ConcurrentKafkaListenerContainerFactory;
import org.springframework.kafka.core.ConsumerFactory;
import org.springframework.kafka.listener.ContainerProperties;
import org.springframework.kafka.listener.DefaultErrorHandler;
import org.springframework.util.backoff.FixedBackOff;

@Configuration
public class KafkaConsumerConfig {
	@Bean
	public ConcurrentKafkaListenerContainerFactory<String, String>
	kafkaListenerContainerFactory(
			ConsumerFactory<String, String> consumerFactory
	) {
		ConcurrentKafkaListenerContainerFactory<String, String> factory =
				new ConcurrentKafkaListenerContainerFactory<>();

		factory.setConsumerFactory(consumerFactory);

		factory.setBatchListener(true);

		factory.getContainerProperties()
				.setAckMode(ContainerProperties.AckMode.MANUAL);
		factory.setConcurrency(3);
		factory.setCommonErrorHandler(
				new DefaultErrorHandler(
						new FixedBackOff(1000L, 3L)
				)
		);

		return factory;
	}
}
