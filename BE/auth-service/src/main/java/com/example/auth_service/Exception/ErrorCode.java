package com.example.auth_service.Exception;

import lombok.AllArgsConstructor;
import lombok.Getter;
import org.springframework.http.HttpStatus;
@Getter
@AllArgsConstructor
public enum ErrorCode {
	SUCCESS(9999, "Success", HttpStatus.OK),
	UNAUTHENTICATED(1000, "Unauthenticated", HttpStatus.UNAUTHORIZED),
	USERNAME_ALREADY_EXISTS(1002, "Username already exists", HttpStatus.CONFLICT),
	INTERNAL_SERVER_ERROR(5000, "Internal server error", HttpStatus.INTERNAL_SERVER_ERROR),
	INVALID_GOOGLE_TOKEN(1003, "Invalid Google token", HttpStatus.BAD_REQUEST),
	GOOGLE_LOGIN_FAILED(1004, "Google login failed", HttpStatus.UNAUTHORIZED),
	INVALID_REFRESH_TOKEN(1005, "Invalid refresh token", HttpStatus.UNAUTHORIZED),
	USER_NOT_FOUND(1001, "User not found", HttpStatus.NOT_FOUND);
	private final int code;
	private final String message;
	private final HttpStatus httpStatus;
}
