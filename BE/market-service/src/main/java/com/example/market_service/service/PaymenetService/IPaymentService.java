package com.example.market_service.service.PaymenetService;

import com.example.market_service.entity.Payment;

public interface IPaymentService {
	String createPayment(Long userId, Long vipPackageId, String method);

	void finalizePayment(String responseCode, String orderInfo);
}
