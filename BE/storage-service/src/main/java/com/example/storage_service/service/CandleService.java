package com.example.storage_service.service;

import com.example.storage_service.Mapper.CandleMapper;
import com.example.storage_service.dto.request.CandleCreationRequest;
import com.example.storage_service.dto.response.CandleResponse;
import com.example.storage_service.entity.Candle;
import com.example.storage_service.repository.CandleRepository;
import jakarta.transaction.Transactional;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
@RequiredArgsConstructor
@Slf4j
public class CandleService {

	private final CandleRepository candleRepository;
	private final CandleMapper candleMapper;
	private final CandleCacheService candleCacheService;

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

	public void savedClosedCandle(CandleCreationRequest request) {
		try {
			Candle candleEntity = candleMapper.toCandle(request);
			candleCacheService.cacheCandle(candleEntity);
			candleRepository.saveAndFlush(candleEntity);
		} catch (Exception e) {
			log.debug(e.getMessage(), e);
		}
	}

	@Transactional
	public void saveClosedCandlesBatch(String symbol, String interval, List<CandleCreationRequest> candles) {
		if (candles == null || candles.isEmpty()) {
			log.info("No candles to save for {} {}", symbol, interval);
			return;
		}

		List<Candle> candlesEntity = candles.stream()
				.map(candleMapper::toCandle)
				.toList();

		candleRepository.saveAllAndFlush(candlesEntity);

		candleCacheService.batchCacheCandles(symbol, interval, candlesEntity);

		log.info("Saved & cached {} closed candles for {} {}", candles.size(), symbol, interval);
	}
}