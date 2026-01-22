package com.example.ws_service.config;

import com.example.ws_service.redis.CandleSubscriber;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.redis.connection.RedisConnectionFactory;
import org.springframework.data.redis.listener.PatternTopic;
import org.springframework.data.redis.listener.RedisMessageListenerContainer;

@Configuration
public class RedisConfig {

	@Bean
	RedisMessageListenerContainer redisContainer(
			RedisConnectionFactory connectionFactory,
			CandleSubscriber candleSubscriber
	) {
		RedisMessageListenerContainer container =
				new RedisMessageListenerContainer();
		container.setConnectionFactory(connectionFactory);

		container.addMessageListener(
				candleSubscriber,
				new PatternTopic("candle:*:*:realtime")
		);
		return container;
	}
	@Bean
	public ObjectMapper objectMapper() {
		return new ObjectMapper();
	}
}
