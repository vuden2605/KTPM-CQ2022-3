package com.example.storage_service.service;

import com.example.storage_service.Mapper.CandleMapper;
import com.example.storage_service.dto.request.CandleCreationRequest;
import com.example.storage_service.dto.response.CandleResponse;
import com.example.storage_service.entity.Candle;
import com.example.storage_service.repository.CandleRepository;
import jakarta.transaction.Transactional;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.Comparator;
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
		}catch (DataIntegrityViolationException e) {
			log.debug("Duplicate candle ignored: {} {} {}",
					request.getSymbol(), request.getInterval(), request.getOpenTime());
		}
		 catch (Exception e) {
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
	public List<CandleCreationRequest> getOlderCandles(
			String symbol,
			String interval,
			Long endTime,
			int limit
	) {
		Pageable pageable = PageRequest.of(0, limit);

		List<Candle> descList = candleRepository
				.findBySymbolAndIntervalAndOpenTimeLessThanOrderByOpenTimeDesc(
						symbol, interval, endTime, pageable
				);

		List<CandleCreationRequest> result = new ArrayList<>();
		for (Candle c : descList) {
			CandleCreationRequest dto = CandleCreationRequest.builder()
					.symbol(c.getSymbol())
					.interval(c.getInterval())
					.openTime(c.getOpenTime())
					.closeTime(c.getCloseTime())
					.open(c.getOpen())
					.high(c.getHigh())
					.low(c.getLow())
					.close(c.getClose())
					.volume(c.getVolume())
					.build();
			result.add(dto);
		}

		result.sort(Comparator.comparingLong(CandleCreationRequest::getOpenTime));
		return result;
	}
}