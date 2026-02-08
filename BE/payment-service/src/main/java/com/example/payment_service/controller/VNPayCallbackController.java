package com.example.payment_service.controller;

import com.example.payment_service.config.VNPayConfig;
import com.example.payment_service.entity.Payment;
import com.example.payment_service.repository.PaymentRepository;
import com.example.payment_service.utils.VNPayUtil;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.Map;

@RestController
@RequestMapping("/vnpay")
@RequiredArgsConstructor
@Slf4j
public class VNPayCallbackController {
	private final VNPayUtil vNPayUtil;
	private final VNPayConfig config;
	private final PaymentRepository paymentRepository;

	@GetMapping("/callback")
	public ResponseEntity<String> vnpayCallback(@RequestParam Map<String, String> params) {
		log.info("VNPay callback received: {}", params);

		Map<String, String> fields = new HashMap<>(params);
		String secureHash = fields.remove("vnp_SecureHash");
		fields.remove("vnp_SecureHashType");

		String hashData = vNPayUtil.buildQueryString(fields);
		String checkHash = vNPayUtil.hmacSHA512(config.getHashSecret(), hashData);

		if (!checkHash.equals(secureHash)) {
			log.error("Invalid signature");
			return ResponseEntity.badRequest().body("Invalid signature");
		}

		String responseCode = params.get("vnp_ResponseCode");
		String orderCode = params.get("vnp_TxnRef");

		Payment payment = paymentRepository.findByOrderId(orderCode)
				.orElseThrow(() -> new RuntimeException("Payment not found"));

		log.info("Payment callback: orderId={}, responseCode={}", orderCode, responseCode);

		return ResponseEntity.ok("Payment processed");
	}
}