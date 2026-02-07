package com.example.market_service.Exception;

import lombok.AllArgsConstructor;
import lombok.Getter;
import org.springframework.http.HttpStatus;

@Getter
@AllArgsConstructor
public enum ErrorCode {
	SUCCESS(9999, "Success", HttpStatus.OK),
	INTERNAL_SERVER_ERROR(100, "Internal server error", HttpStatus.INTERNAL_SERVER_ERROR),
	NOT_FOUND_STORAGE(101, "Storage not found", HttpStatus.NOT_FOUND),
	INVALID_PASSWORD(102, "Invalid password", HttpStatus.UNAUTHORIZED),
	UNAUTHENTICATED(1000, "Unauthenticated", HttpStatus.UNAUTHORIZED),
	USERNAME_ALREADY_EXISTS(1002, "Username already exists", HttpStatus.CONFLICT),
	EMAIL_ALREADY_EXISTS(1006, "Email already exists", HttpStatus.CONFLICT),
	INVALID_GOOGLE_TOKEN(1003, "Invalid Google token", HttpStatus.BAD_REQUEST),
	GOOGLE_LOGIN_FAILED(1004, "Google login failed", HttpStatus.UNAUTHORIZED),
	INVALID_REFRESH_TOKEN(1005, "Invalid refresh token", HttpStatus.UNAUTHORIZED),
	VIP_PACKAGE_NOT_FOUND(2001, "VIP package not found", HttpStatus.NOT_FOUND),
	USER_NOT_FOUND(1001, "User not found", HttpStatus.NOT_FOUND),
	PAYMENT_NOT_FOUND(3001, "Payment not found", HttpStatus.NOT_FOUND);

	private final Integer code;
	private final String message;
	private final HttpStatus httpStatus;
}
