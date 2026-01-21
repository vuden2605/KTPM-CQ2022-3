package com.example.ingest_service.configure;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.java_websocket.client.WebSocketClient;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.reactive.function.client.WebClient;

@Configuration
public class WebClientConfig {
	@Bean
	public WebClient webClient(@Value("${market-service.base-url}") String baseUrl) {
		return WebClient.builder()
				.baseUrl(baseUrl)
				.build();
	}
	@Bean
	public ObjectMapper objectMapper() {
		return new ObjectMapper();
	}

}
