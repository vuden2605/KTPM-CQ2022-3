package com.example.ingest_service.dto.response;

import lombok.Data;

@Data
public class LastOpenTimeResponse {
	private String symbol;
	private String interval;
	private Long lastOpenTime;
}
