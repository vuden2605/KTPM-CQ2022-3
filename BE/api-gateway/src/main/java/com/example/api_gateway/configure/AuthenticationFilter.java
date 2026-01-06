package com.example.api_gateway.configure;

import com.example.api_gateway.dto.request.IntrospectRequest;
import com.example.api_gateway.dto.response.ApiResponse;
import com.example.api_gateway.service.AuthenticationService;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.AccessLevel;
import lombok.RequiredArgsConstructor;
import lombok.experimental.FieldDefaults;
import lombok.experimental.NonFinal;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.cloud.gateway.filter.GatewayFilterChain;
import org.springframework.cloud.gateway.filter.GlobalFilter;
import org.springframework.core.Ordered;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.server.reactive.ServerHttpRequest;
import org.springframework.http.server.reactive.ServerHttpResponse;
import org.springframework.stereotype.Component;
import org.springframework.util.CollectionUtils;
import org.springframework.web.server.ServerWebExchange;
import reactor.core.publisher.Mono;

import java.util.List;


@Component
@Slf4j
@RequiredArgsConstructor
@FieldDefaults(level = AccessLevel.PACKAGE, makeFinal = true)
public class AuthenticationFilter implements GlobalFilter, Ordered {
	AuthenticationService authenticationService;
	ObjectMapper objectMapper;
	private final List<String> publicUrls = List.of(

	);

	@NonFinal
	@Value("${app.api-prefix}")
	private String apiPrefix;

	@Override
	public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
		log.info("AuthenticationFilter called");
//		if(isPublicEndpoint(exchange.getRequest())) {
//			log.info("Public endpoint accessed: {}", exchange.getRequest().getURI().getPath());
//			return chain.filter(exchange);
//		}
		List<String> authHeaders = exchange.getRequest().getHeaders().get(HttpHeaders.AUTHORIZATION);
		if (CollectionUtils.isEmpty(authHeaders))
			return unauthenticated(exchange.getResponse());
		String token = authHeaders.getFirst().replace("Bearer ", "");
		IntrospectRequest introspectRequest = IntrospectRequest.builder()
				.token(token)
				.build();
		log.info("Token extracted: {}", token);

		return authenticationService.introspect(introspectRequest)
				.flatMap(apiResponse -> {
					if (apiResponse.getData().isValid())
						return chain.filter(exchange);
					else {
						log.info("Invalid token: {}", token);
						return unauthenticated(exchange.getResponse());
					}
				}).onErrorResume(throwable -> unauthenticated(exchange.getResponse()));
	}
	private boolean isPublicEndpoint(ServerHttpRequest request) {
		log.info("request path : {}" ,request.getURI().getPath());
		log.info("apiPrefix : {}" ,apiPrefix);
		return publicUrls.stream().anyMatch(publicUrl ->{
			log.info("publicUrl : {}" ,publicUrl);
			return request.getURI().getPath().matches(apiPrefix + publicUrl);
		});

	}


	@Override
	public int getOrder() {
		return -1;
	}

	Mono<Void> unauthenticated(ServerHttpResponse response){
		ApiResponse<?> apiResponse = ApiResponse.builder()
				.code(1401)
				.message("Unauthenticated")
				.build();

		String body = null;
		try {
			body = objectMapper.writeValueAsString(apiResponse);
		} catch (JsonProcessingException e) {
			throw new RuntimeException(e);
		}

		response.setStatusCode(HttpStatus.UNAUTHORIZED);
		response.getHeaders().add(HttpHeaders.CONTENT_TYPE, MediaType.APPLICATION_JSON_VALUE);

		return response.writeWith(
				Mono.just(response.bufferFactory().wrap(body.getBytes())));
	}
}