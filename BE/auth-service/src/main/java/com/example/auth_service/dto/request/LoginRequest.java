package com.example.auth_service.dto.request;

import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class LoginRequest {
	private String userName;
	private String password;
}
