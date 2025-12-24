package com.example.market_service.entity;

import jakarta.persistence.*;
import lombok.*;

import java.math.BigDecimal;
import java.time.Instant;

@Entity
@Table(
		name = "candles",
		uniqueConstraints = {
				@UniqueConstraint(
						name = "uk_symbol_interval_open_time",
						columnNames = {"symbol", "interval", "open_time"}
				)
		},
		indexes = {
				@Index(name = "idx_symbol_interval_open_time", columnList = "symbol, interval, open_time DESC")
		}
)
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Candle {

	@Id
	@GeneratedValue(strategy = GenerationType.IDENTITY)
	private Long id;

	@Column(nullable = false, length = 20)
	private String symbol;

	@Column(nullable = false, length = 5)
	private String interval;

	@Column(name = "open_time", nullable = false)
	private Instant openTime;

	@Column(name = "close_time", nullable = false)
	private Instant closeTime;

	@Column(nullable = false, precision = 19, scale = 8)
	private BigDecimal open;

	@Column(nullable = false, precision = 19, scale = 8)
	private BigDecimal high;

	@Column(nullable = false, precision = 19, scale = 8)
	private BigDecimal low;

	@Column(nullable = false, precision = 19, scale = 8)
	private BigDecimal close;

	@Column(nullable = false, precision = 19, scale = 8)
	private BigDecimal volume;

	@Column(name = "created_at", nullable = false, updatable = false)
	@Builder.Default
	private Instant createdAt = Instant.now();

}

