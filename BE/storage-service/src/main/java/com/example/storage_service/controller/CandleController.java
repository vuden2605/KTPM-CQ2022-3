package com.example.storage_service.controller;

import com.example.storage_service.dto.request.CandleBatchRequest;
import com.example.storage_service.dto.request.CandleCreationRequest;
import com.example.storage_service.dto.response.ApiResponse;
import com.example.storage_service.dto.response.CandleResponse;
import com.example.storage_service.entity.Candle;
import com.example.storage_service.service.CandleService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.bind.annotation.CrossOrigin;

import java.util.List;

@RestController
@CrossOrigin(origins = "http://localhost:5173")
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
	@GetMapping("/recent")
	public ApiResponse<List<Candle>> getRecentCandles(
			@RequestParam("symbol") String symbol,
			@RequestParam("interval") String interval,
			@RequestParam(value = "pageSize", defaultValue = "1000") int pageSize,
			@RequestParam(value = "page", defaultValue = "0") int page
	) {
		if (pageSize <= 0) pageSize = 1;
		if (pageSize > 1000) pageSize = 1000;

		List<Candle> candles =
				candleService.getRecentCandles(symbol, interval, pageSize, page);

		return ApiResponse.<List<Candle>>builder()
				.data(candles)
				.message("Fetched recent candles successfully")
				.build();
	}
}
