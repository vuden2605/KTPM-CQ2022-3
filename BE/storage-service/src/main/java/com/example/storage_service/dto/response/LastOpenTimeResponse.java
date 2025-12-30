package com.example.storage_service.dto.response;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@AllArgsConstructor
@NoArgsConstructor
public class LastOpenTimeResponse {
	private String symbol;
	private String interval;
	private Long lastOpenTime;
}
