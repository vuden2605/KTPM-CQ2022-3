package com.example.auth_service.dto.request;

import lombok.Data;

@Data
public class IntrospectRequest {
	private String token;
}
