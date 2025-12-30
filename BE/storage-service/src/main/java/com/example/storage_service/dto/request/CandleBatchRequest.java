package com.example.storage_service.dto.request;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

@Data
@Builder
@AllArgsConstructor
@NoArgsConstructor
public class CandleBatchRequest {
	private String symbol;
	private String interval;
	private List<CandleCreationRequest> candles;
}
