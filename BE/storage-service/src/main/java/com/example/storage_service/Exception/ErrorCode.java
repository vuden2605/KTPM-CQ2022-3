package com.example.storage_service.Exception;

import lombok.AllArgsConstructor;
import lombok.Getter;
import org.springframework.http.HttpStatus;
@Getter
@AllArgsConstructor
public enum ErrorCode {
	SUCCESS(9999, "Success", HttpStatus.OK),
	INTERNAL_SERVER_ERROR(100, "Internal server error", HttpStatus.INTERNAL_SERVER_ERROR),
	NOT_FOUND_STORAGE(101, "Storage not found", HttpStatus.NOT_FOUND);
	private final Integer code;
	private final String message;
	private final HttpStatus httpStatus;
}
