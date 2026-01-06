package com.example.auth_service.dto.response;

import lombok.Builder;
import lombok.Data;

@Data
@Builder
public class IntrospectResponse {
	private boolean isValid;
}
