package com.example.storage_service.service;

import com.example.storage_service.Mapper.CandleMapper;
import com.example.storage_service.dto.request.CandleCreationRequest;
import com.example.storage_service.dto.response.CandleResponse;
import com.example.storage_service.entity.Candle;
import com.example.storage_service.repository.CandleRepository;
import jakarta.transaction.Transactional;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.cache.annotation.CacheEvict;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.web.bind.annotation.GetMapping;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;

@Service
@RequiredArgsConstructor
@Slf4j
public class CandleService {

	private final CandleRepository candleRepository;
	private final CandleMapper candleMapper;

	public Long getLastOpenTime(String symbol, String interval) {
		return candleRepository.findLastOpenTime(symbol, interval);
	}

	public CandleResponse createCandle(CandleCreationRequest request) {
		Candle candle = candleMapper.toCandle(request);
		try {
			Candle savedCandle = candleRepository.saveAndFlush(candle);
			return candleMapper.toCandleResponse(savedCandle);
		} catch (Exception e) {
			log.debug(e.getMessage(), e);
			throw new RuntimeException(e);
		}
	}
	@CacheEvict(
			value = {
					"recent-candles-1m",
					"recent-candles-5m",
					"recent-candles-15m",
					"recent-candles-1h"
			},
			allEntries = true
	)
	public void upsertCandle(
			String symbol,
			String interval,
			Long openTime,
			Long closeTime,
			BigDecimal open,
			BigDecimal high,
			BigDecimal low,
			BigDecimal close,
			BigDecimal volume
	) {
		candleRepository.upsertCandle(
				symbol,
				interval,
				openTime,
				closeTime,
				open,
				high,
				low,
				close,
				volume
		);
	}
	@Cacheable(
			value = "'recent-candles-' + #interval",
			key = "#symbol + ':' + #page + ':' + #pageSize"
	)
	public List<Candle> getRecentCandles(
			String symbol,
			String interval,
			int pageSize,
			int page
	) {
		Pageable pageable = PageRequest.of(page, pageSize);

		List<Candle> candles = candleRepository.findRecentCandles(symbol, interval, pageable);

		candles.sort(Comparator.comparingLong(Candle::getOpenTime));
		return candles;
	}
}