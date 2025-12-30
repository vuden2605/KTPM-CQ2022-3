package com.example.storage_service.Mapper;

import com.example.storage_service.dto.request.CandleCreationRequest;
import com.example.storage_service.dto.response.CandleResponse;
import com.example.storage_service.entity.Candle;
import org.mapstruct.Mapper;

import java.time.Instant;

@Mapper(componentModel = "spring")
public interface CandleMapper {
	Candle toCandle(CandleCreationRequest request);
	CandleResponse toCandleResponse(Candle candle);
}
