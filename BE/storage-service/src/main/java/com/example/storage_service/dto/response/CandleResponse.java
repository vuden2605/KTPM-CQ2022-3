package com.example.storage_service.dto.response;

import com.fasterxml.jackson.annotation.JsonFormat;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.time.Instant;
@Data
@Builder
@AllArgsConstructor
@NoArgsConstructor
public class CandleResponse {
	private String symbol;
	private String interval;
	private Long openTime;
	private Long closeTime;
	private BigDecimal open;
	private BigDecimal high;
	private BigDecimal low;
	private BigDecimal close;
	private BigDecimal volume;
}
