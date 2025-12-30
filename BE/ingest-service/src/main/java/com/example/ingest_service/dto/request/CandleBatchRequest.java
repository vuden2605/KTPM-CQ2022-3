package com.example.ingest_service.dto.request;

import java.util.List;

public class CandleBatchRequest {
	public String symbol;
	public String interval;
	public List<Candle> candles;
}
