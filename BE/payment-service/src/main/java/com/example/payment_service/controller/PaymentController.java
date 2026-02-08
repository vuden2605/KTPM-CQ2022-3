package com.example.payment_service.controller;

import com.example.payment_service.dto.request.PaymentCreationRequest;
import com.example.payment_service.dto.response.ApiResponse;
import com.example.payment_service.service.PaymentService.IPaymentService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/payments")
@RequiredArgsConstructor
@Slf4j
public class PaymentController {
	private final IPaymentService paymentService;

	@PostMapping
	public ApiResponse<String> createPayment(
			@RequestHeader("X-User-Id") Long userId,
			@RequestBody @Valid PaymentCreationRequest request) {
		log.info("Creating payment for userId: {}, vipPackageId: {}", userId, request.getVipPackageId());

		String paymentUrl = paymentService.createPayment(
				userId,
				request.getVipPackageId(),
				request.getPaymentMethod()
		);

		return ApiResponse.<String>builder()
				.message("Payment created successfully")
				.data(paymentUrl)
				.build();
	}

	@PostMapping("/finalize")
	public ApiResponse<String> finalizePayment(
			@RequestParam String responseCode,
			@RequestParam String orderId) {
		log.info("Finalizing payment: orderId={}, responseCode={}", orderId, responseCode);

		paymentService.finalizePayment(responseCode, orderId);

		return ApiResponse.<String>builder()
				.message("Payment finalized successfully")
				.build();
	}
}