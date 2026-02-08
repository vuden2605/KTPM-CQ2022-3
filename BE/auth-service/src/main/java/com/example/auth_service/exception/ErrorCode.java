package com.example.auth_service.exception;

import lombok.Getter;
import org.springframework.http.HttpStatus;

@Getter
public enum ErrorCode {
	USER_NOT_FOUND(1001, "User not found", HttpStatus.NOT_FOUND),
	INVALID_PASSWORD(1002, "Invalid password", HttpStatus.UNAUTHORIZED),
	INVALID_REFRESH_TOKEN(1003, "Invalid refresh token", HttpStatus.UNAUTHORIZED),
	INVALID_GOOGLE_TOKEN(1004, "Invalid Google token", HttpStatus.UNAUTHORIZED),
	GOOGLE_LOGIN_FAILED(1005, "Google login failed", HttpStatus.INTERNAL_SERVER_ERROR),
	USER_ALREADY_EXISTS(1006, "User already exists", HttpStatus.BAD_REQUEST),
	USERNAME_ALREADY_EXISTS(1008, "Username already exists", HttpStatus.BAD_REQUEST),
	EMAIL_ALREADY_EXISTS(1009, "Email already exists", HttpStatus.BAD_REQUEST),
	UNAUTHENTICATED(1007, "User is not authenticated", HttpStatus.UNAUTHORIZED);

	private final int code;
	private final String message;
	private final HttpStatus httpStatus;

	ErrorCode(int code, String message, HttpStatus httpStatus) {
		this.code = code;
		this.message = message;
		this.httpStatus = httpStatus;
	}
}