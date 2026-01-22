package com.example.ingest_service.configure;

import com.example.ingest_service.dto.response.ApiResponseLong;
import com.example.ingest_service.dto.response.LastOpenTimeResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

import java.util.Optional;

@Component
@RequiredArgsConstructor
@Slf4j
public class StorageServiceWebClient {
	private final WebClient webClient;

	public Optional<Long> getLastOpenTime(String symbol, String interval) {

		ApiResponseLong response = webClient.get()
				.uri(uriBuilder -> uriBuilder
						.path("/candles/last-open-time")
						.queryParam("symbol", symbol)
						.queryParam("interval", interval)
						.build())
				.retrieve()
				.bodyToMono(ApiResponseLong.class)
				.block();
		return Optional.ofNullable(response).map(ApiResponseLong::getData);
	}

}
