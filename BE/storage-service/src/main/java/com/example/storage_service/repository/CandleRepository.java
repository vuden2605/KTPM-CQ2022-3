package com.example.storage_service.repository;

import com.example.storage_service.entity.Candle;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.math.BigDecimal;
import java.util.List;

@Repository
public interface CandleRepository extends JpaRepository<Candle, Long> {
	@Query("""
		SELECT MAX(c.openTime) FROM Candle c
		WHERE c.symbol = :symbol AND c.interval = :interval
	""")
	Long findLastOpenTime(@Param("symbol") String symbol,
	                      @Param("interval") String interval);
	List<Candle> findBySymbolAndIntervalAndOpenTimeLessThanOrderByOpenTimeDesc(
			String symbol,
			String interval,
			Long endTime,
			Pageable pageable
	);
}
