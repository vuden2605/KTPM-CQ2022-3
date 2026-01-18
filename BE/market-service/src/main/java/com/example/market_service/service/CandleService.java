package com.example.market_service.service;

import com.example.market_service.Mapper.CandleMapper;
import com.example.market_service.dto.request.CandleCreationRequest;
import com.example.market_service.dto.response.CandleResponse;
import com.example.market_service.entity.Candle;
import com.example.market_service.repository.CandleRepository;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.transaction.Transactional;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.cache.annotation.CacheEvict;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.util.Collections;
import java.util.Comparator;
import java.util.List;
import java.util.Set;

@Service
@RequiredArgsConstructor
@Slf4j
public class CandleService {

	private final CandleRepository candleRepository;
	private final CandleMapper candleMapper;
	private final RedisTemplate<String, String> redisTemplate;
	private final ObjectMapper objectMapper;
	private final JdbcTemplate jdbcTemplate;

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

	public List<Candle> getRecentCandles(
			String symbol,
			String interval,
			boolean isVip
	) {
		int limit = 0;
		if (!isVip) {
			limit = 1000;
		}
		else limit = 1500;
		String key = "candles:" + symbol + ":" + interval;
		Long total = redisTemplate.opsForZSet().zCard(key);
		if (total == null || total == 0) {
			return getRecentCandlesFromDb(symbol, interval, limit);
		}
		long start = Math.max(0, total - limit);
		long end = total - 1;
		Set<String> raw = redisTemplate.opsForZSet()
				.range(key, start, end);
		if (raw == null || raw.isEmpty()) return getRecentCandlesFromDb(symbol, interval, limit);
		return raw.stream()
				.map(json -> {
					try {
						return objectMapper.readValue(json, Candle.class);
					} catch (JsonProcessingException e) {
						throw new RuntimeException(e);
					}
				})
				.toList();
	}
	public List<Candle> getRecentCandlesFromDb(
			String symbol,
			String interval,
			int limit
	) {
		Pageable pageable = PageRequest.of(0, limit);

		List<Candle> candles = candleRepository.findRecentCandles(symbol, interval, pageable);
		candles.sort(Comparator.comparingLong(Candle::getOpenTime));
		return candles;
	}
	@Transactional
	public void batchInsert(List<Candle> candles) {
		String sql = """
        INSERT INTO candles
        (symbol,interval,open_time,close_time,open,high,low,close,volume)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT DO NOTHING
    """;

		jdbcTemplate.batchUpdate(sql, candles, 500,
				(ps, c) -> {
					ps.setString(1, c.getSymbol());
					ps.setString(2, c.getInterval());
					ps.setLong(3, c.getOpenTime());
					ps.setLong(4, c.getCloseTime());
					ps.setBigDecimal(5, c.getOpen());
					ps.setBigDecimal(6, c.getHigh());
					ps.setBigDecimal(7, c.getLow());
					ps.setBigDecimal(8, c.getClose());
					ps.setBigDecimal(9, c.getVolume());
				}
		);
	}

}