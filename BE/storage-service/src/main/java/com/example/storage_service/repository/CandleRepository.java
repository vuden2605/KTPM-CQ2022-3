package com.example.storage_service.repository;

import com.example.storage_service.entity.Candle;
import jakarta.transaction.Transactional;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
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

	@Query("SELECT c FROM Candle c WHERE c.symbol = :symbol AND c. interval = :interval ORDER BY c.openTime DESC")
	List<Candle> findRecentCandles(
			@Param("symbol") String symbol,
			@Param("interval") String interval,
			Pageable pageable
	);

	@Modifying
	@Transactional
	@Query(value = """
        INSERT INTO candles (
            symbol,
            interval,
            open_time,
            close_time,
            open,
            high,
            low,
            close,
            volume
        ) VALUES (
            :symbol,
            :interval,
            :openTime,
            :closeTime,
            :open,
            :high,
            :low,
            :close,
            :volume
        )
        ON CONFLICT (symbol, interval, open_time)
        DO UPDATE SET
            close_time = EXCLUDED.close_time,
            open       = EXCLUDED.open,
            high       = EXCLUDED.high,
            low        = EXCLUDED.low,
            close      = EXCLUDED.close,
            volume     = EXCLUDED.volume
        """, nativeQuery = true)
	void upsertCandle(
			@Param("symbol") String symbol,
			@Param("interval") String interval,
			@Param("openTime") Long openTime,
			@Param("closeTime") Long closeTime,
			@Param("open") BigDecimal open,
			@Param("high") BigDecimal high,
			@Param("low") BigDecimal low,
			@Param("close") BigDecimal close,
			@Param("volume") BigDecimal volume
	);
}
