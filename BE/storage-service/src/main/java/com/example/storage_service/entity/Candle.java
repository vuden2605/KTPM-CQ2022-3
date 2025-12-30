package com.example.storage_service.entity;

import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate. annotations.UpdateTimestamp;

import java.math.BigDecimal;
import java.time. Instant;

@Entity
@Table(
		name = "candles",
		uniqueConstraints = @UniqueConstraint(
				name = "uk_candles_symbol_interval_opentime",
				columnNames = {"symbol", "interval", "open_time"}
		),
		indexes = {
				@Index(name = "idx_candles_symbol_interval_time", columnList = "symbol, interval, open_time DESC")
		}
)
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Candle {

	@Id
	@GeneratedValue(strategy = GenerationType. IDENTITY)
	private Long id;

	@Column(nullable = false, length = 20)
	private String symbol;

	@Column(nullable = false, length = 10)
	private String interval;

	@Column(name = "open_time", nullable = false)
	private Long openTime;

	@Column(name = "close_time", nullable = false)
	private Long closeTime;

	@Column(nullable = false, precision = 20, scale = 8)
	private BigDecimal open;

	@Column(nullable = false, precision = 20, scale = 8)
	private BigDecimal high;

	@Column(nullable = false, precision = 20, scale = 8)
	private BigDecimal low;

	@Column(nullable = false, precision = 20, scale = 8)
	private BigDecimal close;

	@Column(nullable = false, precision = 30, scale = 12)
	private BigDecimal volume;

	@CreationTimestamp
	@Column(name = "created_at", updatable = false)
	private Instant createdAt;

	@UpdateTimestamp
	@Column(name = "updated_at")
	private Instant updatedAt;
}