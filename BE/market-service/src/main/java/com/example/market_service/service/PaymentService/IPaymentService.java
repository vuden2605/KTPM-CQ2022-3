package com.example.market_service.service.PaymentService;

public interface IPaymentService {
	String createPayment(Long userId, Long vipPackageId, String method);

	void finalizePayment(String responseCode, String orderInfo);
}
