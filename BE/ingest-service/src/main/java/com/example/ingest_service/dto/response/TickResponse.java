package com.example.ingest_service.dto.response;

import lombok.Builder;
import lombok.Data;

import java.math.BigDecimal;

@Data
@Builder
public class TickResponse {
	private String symbol;
	private BigDecimal price;
	private BigDecimal volume;
	private Long tradeId;
	private Boolean maker;
	private Long eventTime;
}
