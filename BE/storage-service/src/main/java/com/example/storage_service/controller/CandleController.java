package com.example.storage_service.controller;

import com.example.storage_service.dto.request.CandleBatchRequest;
import com.example.storage_service.dto.request.CandleCreationRequest;
import com.example.storage_service.dto.response.ApiResponse;
import com.example.storage_service.dto.response.CandleResponse;
import com.example.storage_service.service.CandleService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequiredArgsConstructor
@RequestMapping("/candles")
@Slf4j
public class CandleController {
	private final CandleService candleService;
	@PostMapping
	public ApiResponse<CandleResponse> createCandle(@RequestBody CandleCreationRequest request) {
		log.info("Received request to create candle: {}", request);
		CandleResponse candleResponse = candleService.createCandle(request);
		return ApiResponse.<CandleResponse>builder()
				.data(candleResponse)
				.message("Candle created successfully")
				.build();
	}
	@PostMapping("/batch")
	public ApiResponse<Void> saveCandlesBatch(
			@RequestBody @Valid CandleBatchRequest request) {
		candleService.saveClosedCandlesBatch(request.getSymbol(), request.getInterval(), request.getCandles());
		return ApiResponse.<Void>builder()
				.message("Candles batch saved successfully")
				.build();
	}
	@GetMapping
	public ApiResponse<String> getCandle() {
		return ApiResponse.<String>builder()
				.data("Storage Service is up and running")
				.message("Service status checked successfully")
				.build();
	}
	@GetMapping("/last-open-time")
	public ApiResponse<Long> getLastOpenTime(
			@RequestParam("symbol") String symbol,
			@RequestParam("interval") String interval) {
		Long lastOpenTime = candleService.getLastOpenTime(symbol, interval);
		return ApiResponse.<Long>builder()
				.data(lastOpenTime)
				.message("Last open time retrieved successfully")
				.build();
	}

}
