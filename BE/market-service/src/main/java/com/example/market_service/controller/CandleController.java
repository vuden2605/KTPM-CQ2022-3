package com.example.market_service.controller;

import com.example.market_service.dto.request.CandleCreationRequest;
import com.example.market_service.dto.response.ApiResponse;
import com.example.market_service.dto.response.CandleResponse;
import com.example.market_service.entity.Candle;
import com.example.market_service.service.CandleService.ICandleService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.apache.catalina.security.SecurityUtil;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.bind.annotation.CrossOrigin;

import java.util.List;

@RestController
@CrossOrigin(origins = "*")
@RequiredArgsConstructor
@RequestMapping("/candles")
@Slf4j
public class CandleController {
	private final ICandleService candleService;
	@PostMapping
	public ApiResponse<CandleResponse> createCandle(@RequestBody CandleCreationRequest request) {
		log.info("Received request to create candle: {}", request);
		CandleResponse candleResponse = candleService.createCandle(request);
		return ApiResponse.<CandleResponse>builder()
				.data(candleResponse)
				.message("Candle created successfully")
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
			@RequestHeader(value = "X-User-Role", required = false) String userRole,
			@RequestParam("symbol") String symbol,
			@RequestParam("interval") String interval) {
		boolean isVip = "VIP".equalsIgnoreCase(userRole);
		List<Candle> candles = candleService.getRecentCandles(symbol, interval, isVip);

		return ApiResponse.<List<Candle>>builder()
				.data(candles)
				.message("Fetched recent candles successfully")
				.build();
	}

	@GetMapping("/before-time")
	public ApiResponse<List<Candle>> getCandlesBeforeTime(
			@RequestParam("symbol") String symbol,
			@RequestParam("interval") String interval,
			@RequestParam("beforeTime") Long beforeTime) {
		List<Candle> candles = candleService.getCandlesBeforeOpenTime(symbol, interval, beforeTime);
		return ApiResponse.<List<Candle>>builder()
				.data(candles)
				.message("Fetched candles before specified time successfully")
				.build();
	}

	@GetMapping("/between-times")
	public ApiResponse<List<Candle>> getCandlesBetweenTimes(
			@RequestParam("symbol") String symbol,
			@RequestParam("interval") String interval,
			@RequestParam("startTime") Long startTime,
			@RequestParam("endTime") Long endTime) {
		List<Candle> candles = candleService.getCandlesBetweenOpenTimes(
				symbol,
				interval,
				startTime,
				endTime);
		return ApiResponse.<List<Candle>>builder()
				.data(candles)
				.message("Fetched candles between specified times successfully")
				.build();
	}

	@GetMapping("/latest-candle")
	public ApiResponse<List<Candle>> getLatestCandle(
			@RequestParam("interval") String interval) {

		return ApiResponse.<List<Candle>>builder()
				.data(candleService.getLatestPrice(interval))
				.message("Fetched latest candle successfully")
				.build();
	}
}
