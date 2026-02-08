package com.example.api_gateway.configure;

import com.example.api_gateway.repository.AuthenticationServiceClient;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.reactive.function.client.support.WebClientAdapter;
import org.springframework.web.service.invoker.HttpServiceProxyFactory;

@Configuration
public class WebClientConfigure {
	@Value("${AUTH_SERVICE_URL:http://localhost:8088}")
	private String authServiceUrl;
	@Bean
	WebClient webClient(){
		return WebClient.builder()
				.baseUrl(authServiceUrl)
				.build();
	}
	@Bean
	AuthenticationServiceClient authenticationServiceClient(WebClient webClient){
		HttpServiceProxyFactory httpServiceProxyFactory = HttpServiceProxyFactory
				.builderFor(WebClientAdapter.create(webClient)).build();

		return httpServiceProxyFactory.createClient(AuthenticationServiceClient.class);
	}
}
