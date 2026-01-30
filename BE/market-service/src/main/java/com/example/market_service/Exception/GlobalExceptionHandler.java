package com.example.market_service.Exception;

import com.example.market_service.dto.response.ApiResponse;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ControllerAdvice;
import org.springframework.web.bind.annotation.ExceptionHandler;

import java.util.Objects;

@ControllerAdvice
@lombok.extern.slf4j.Slf4j
public class GlobalExceptionHandler {
	@ExceptionHandler(Exception.class)
	public ResponseEntity<ApiResponse<?>> handleGeneralException(Exception e) {
		log.error("Generic Exception: ", e);
		ApiResponse<?> response = ApiResponse.builder()
				.code(ErrorCode.INTERNAL_SERVER_ERROR.getCode())
				.message(e.getMessage())
				.build();
		return ResponseEntity.status(ErrorCode.INTERNAL_SERVER_ERROR.getHttpStatus()).body(response);
	}

	@ExceptionHandler(AppException.class)
	public ResponseEntity<ApiResponse<?>> handleAppException(AppException e) {
		ErrorCode errorCode = e.getErrorCode();
		ApiResponse<?> response = ApiResponse.builder()
				.code(errorCode.getCode())
				.message(errorCode.getMessage())
				.build();
		return ResponseEntity.status(errorCode.getHttpStatus()).body(response);
	}

	@ExceptionHandler(MethodArgumentNotValidException.class)
	public ResponseEntity<ApiResponse<?>> handleValidationException(MethodArgumentNotValidException e) {
		String errorMessage = Objects.requireNonNull(e.getBindingResult().getFieldError()).getDefaultMessage();
		ErrorCode error = ErrorCode.valueOf(errorMessage);
		ApiResponse<?> response = ApiResponse.builder()
				.code(error.getCode())
				.message(error.getMessage())
				.build();
		return ResponseEntity.status(error.getHttpStatus()).body(response);
	}
}
