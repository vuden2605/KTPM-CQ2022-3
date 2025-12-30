package com.example.ingest_service.dto.request;

import lombok.*;

import java.math.BigDecimal;

@Builder
@Data
@NoArgsConstructor
@AllArgsConstructor
public class Candle {

	private String symbol;

	private String interval;

	private Long openTime;

	private Long closeTime;

	private BigDecimal open;

	private BigDecimal high;

	private BigDecimal low;

	private BigDecimal close;

	private BigDecimal volume;

	private Boolean isClosed;
}



