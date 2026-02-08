package com.example.api_gateway.configure;

import lombok.extern.slf4j.Slf4j;
import org.springframework.cloud.gateway.filter.GatewayFilterChain;
import org.springframework.cloud.gateway.filter.GlobalFilter;
import org.springframework.core.Ordered;
import org.springframework.http.server.reactive.ServerHttpRequest;
import org.springframework.stereotype.Component;
import org.springframework.web.server.ServerWebExchange;
import reactor.core.publisher.Mono;

@Component
@Slf4j
public class DebugForwardFilter implements GlobalFilter, Ordered {

	@Override
	public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
		return chain.filter(exchange).then(
				Mono.fromRunnable(() -> {
					ServerHttpRequest req = exchange.getRequest();
					log.info(">>> AFTER STRIP - FORWARDED PATH: {}", req.getURI().getPath());
					log.info(">>> AFTER STRIP - FORWARDED URI : {}", req.getURI());
				})
		);
	}

	@Override
	public int getOrder() {
		return Ordered.LOWEST_PRECEDENCE;
	}
}
